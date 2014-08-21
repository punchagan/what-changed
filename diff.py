#!/usr/bin/env python

from __future__ import absolute_import, print_function

# 3rd party library
import astroid

# Local library
from util import dotted_getattr, is_public, parse_file

class Diff(object):

    def __new__(cls, old, new):
        """Return None if there is no diff.

        Also, sets the attributes of the object, based on the computed diff.

        """

        diff = cls.compute_diff(old, new)

        if len(filter(None, diff.values())) > 0:
            obj = super(Diff, cls).__new__(cls, old, new)
            for attr, value in diff.iteritems():
                setattr(obj, attr, value)

        else:
            obj = None

        return obj

    def __init__(self, old, new):
        """Constructor. """

        self.old = old
        self.new = new

    @classmethod
    def compute_diff(cls, old, new):
        raise NotImplementedError

    ## FIXME: This should really be a part of a "function collection" kind of a
    ## class, not the diff class.
    @classmethod
    def _diff_functions(cls, old, new):
        diff = {}

        old_functions = cls.interesting_functions(old) if old is not None else {}
        new_functions = cls.interesting_functions(new) if new is not None else {}

        old_names = set(old_functions.keys())
        new_names = set(new_functions.keys())

        changed_functions = diff.setdefault('changed_functions', {})

        for name in (old_names | new_names):
            function_diff = diff_functions(
                old_functions.get(name, None), new_functions.get(name, None)
            )
            if function_diff is not None:
                changed_functions[name] = function_diff

        return diff


class ClassDiff(Diff):

    def __init__(self, old, new):
        """Constructor. """

        super(ClassDiff, self).__init__(old, new)
        ## FIXME: We should allow class names to change, may be...
        self.name = self.old.name if old is not None else self.new.name

    @classmethod
    def compute_diff(cls, old, new):
        diff = {}
        interested_in = {
            'bases': 'bases',
            ## FIXME: do we really need this?
            'decorators': 'decorators',
        }

        for name, attr in interested_in.iteritems():
            a = dotted_getattr(old, attr) if old is not None else None
            b = dotted_getattr(new, attr) if new is not None else None
            diff[name] = compare(a, b)

        o = old.body if old is not None else None
        n = new.body if new is not None else None

        diff.update(cls._diff_functions(o, n))

        return diff

    @classmethod
    def interesting_functions(cls, klass):
        functions = {
            node.name: node for node in klass

            if isinstance(node, astroid.Function) and
            (is_public(node) or node.name in set(['__init__', '__call__']))
        }

        return functions

    def __repr__(self):
        text = ''

        if self.bases:
            old_bases, new_bases = self.bases
            if self.old is not None:
                text += '- class %s(%s):\n' % (
                    self.old.name,
                    ', '.join([b.as_string() for b in old_bases or []])
                )

            if self.new is not None:
                text += '+ class %s(%s):\n' % (
                    self.new.name,
                    ', '.join([b.as_string() for b in new_bases or []])
                )

        else:
            bases = self.old.basenames
            text += 'class %s(%s):\n' % (self.name, ', '.join(bases or []))

        ## FIXME: duplicated in modules repr...
        if self.changed_functions:
            for _, function in self.changed_functions.iteritems():
                text += repr(function)

            text += '\n'

        text = text.replace('\n', '\n' + 4 * ' ').strip()
        text += '\n'

        return text


class FunctionDiff(Diff):

    def __init__(self, old, new):
        """Constructor."""

        super(FunctionDiff, self).__init__(old, new)
        if not (old is None or new is None):
            ## FIXME: We should allow function names to change, may be...
            assert old.name == new.name

        self.name = old.name if old is not None else new.name

    @classmethod
    def compute_diff(cls, old, new):
        ## FIXME: allow one of old or new to be None.
        diff = {}

        interesting_properties = {
            'arguments': 'args.args',
            'defaults': 'args.defaults',
            'vararg': 'args.vararg',
            'kwarg': 'args.kwarg',
            ## FIXME: do we really need this?
            'decorators': 'decorators',
        }

        for name, attr in interesting_properties.iteritems():
            a = dotted_getattr(old, attr) if old is not None else None
            b = dotted_getattr(new, attr) if new is not None else None
            diff[name] = compare(a, b)

        return diff

    def __repr__(self):
        old = '- %s\n' % self._get_signature('old') if self.old is not None else ''
        new = '+ %s\n' % self._get_signature('new') if self.new is not None else ''
        text = "%s%s\n" % (old, new)
        return text

    def _get_signature(self, version):
        assert version in ('old', 'new')
        f = getattr(self, version, None)

        argnames = [arg.name for arg in f.args.args]
        n = len(argnames)
        d = len(f.args.defaults)

        def to_string(el):
            return el if isinstance(el, basestring) else el.as_string()

        argnames = [
            to_string(name)

            if i < (n - d)
            else '%s=%s' % (to_string(name), to_string(f.args.defaults[i-n]))

            for i, name in enumerate(argnames)

        ]

        if f.args.vararg is not None:
            argnames.append('*%s' % f.args.vararg)

        if f.args.kwarg is not None:
            argnames.append('**%s' % f.args.kwarg)

        return "def %s(%s)" % (f.name, ', '.join(argnames))


class ModuleDiff(Diff):

    def __init__(self, old, new):
        """Constructor. """

        super(ModuleDiff, self).__init__(old, new)
        ## FIXME: We should allow class names to change, may be...
        self.name = self.old.name if old is not None else self.new.name

    @classmethod
    def compute_diff(cls, old, new):
        diff = cls._diff_functions(old.body, new.body)
        d2 = cls._diff_classes(old.body, new.body)
        diff.update(d2)
        return diff

    @staticmethod
    def interesting_functions(module):
        functions = {
            node.name: node for node in module
            if isinstance(node, astroid.Function) and is_public(node)
        }

        return functions


    @classmethod
    def _get_public_classes(cls, module):
        public_classes = {
            node.name: node for node in module
            if isinstance(node, astroid.Class) and is_public(node)
        }
        return public_classes


    @classmethod
    def _diff_classes(cls, old, new):
        diff = {}

        old_classes = cls._get_public_classes(old)
        new_classes = cls._get_public_classes(new)

        old_names = set(old_classes.keys())
        new_names = set(new_classes.keys())

        changed_classes = diff.setdefault('changed_classes', {})

        for name in (old_names | new_names):
            class_diff = diff_classes(
                old_classes.get(name, None), new_classes.get(name, None)
            )
            if class_diff is not None:
                changed_classes[name] = class_diff

        return diff

    def __repr__(self):
        # FIXME: make this all into a template!

        text = ''
        if self.old is not None:
            text += '- %s\n' % self.old.file
        if self.new is not None:
            text += '+ %s\n' % self.new.file
        text += '\n'

        if self.changed_functions:
            text += '\n'
            for _, function in self.changed_functions.iteritems():
                text += repr(function)
            text += '\n'

        if self.changed_classes:
            text += '\n'
            for _, klass in self.changed_classes.iteritems():
                text += repr(klass)
            text += '\n'

        text += '\n'

        return text


def diff_files(old, new):
    return ModuleDiff(parse_file(old), parse_file(new))


def diff_functions(old, new):
    return FunctionDiff(old, new)


def diff_classes(old, new):
    return ClassDiff(old, new)


def compare(a, b):
    """ Compare everything under the sun! """

    if type(a) != type(b):
        return (a, b)

    elif isinstance(a, basestring):
        return None if a == b else (a, b)

    elif isinstance(a, list):
        if len(a) != len(b):
            return (a, b)

        else:
            for i, item in enumerate(a):
                if compare(item, b[i]) is not None:
                    return (a, b)

    elif hasattr(a, 'as_string') and hasattr(b, 'as_string'):
        a, b = a.as_string(), b.as_string()
        return None if a == b else (a, b)

    return None
