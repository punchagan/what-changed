#!/usr/bin/env python

from __future__ import absolute_import, print_function

import ast

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

    @classmethod
    def _diff_functions(cls, old, new):
        diff = {}

        old_functions = cls.interesting_functions(old)
        new_functions = cls.interesting_functions(new)

        old_names = set(old_functions.keys())
        new_names = set(new_functions.keys())

        removed_functions = old_names - new_names
        added_functions = new_names - old_names

        diff['removed_functions'] = removed_functions
        diff['added_functions'] = added_functions
        changed_functions = diff.setdefault('changed_functions', {})

        for name in (old_names & new_names):
            function_diff = diff_functions(old_functions[name], new_functions[name])
            if function_diff is not None:
                changed_functions['name'] = function_diff

        return diff


class ClassDiff(Diff):

    @classmethod
    def compute_diff(cls, old, new):
        diff = {}
        interested_in = {
            'bases': 'bases',
            'decorator_list': 'decorator_list',
        }

        for name, attr in interested_in.iteritems():
            a = dotted_getattr(old, attr)
            b = dotted_getattr(new, attr)
            diff[name] = compare(a, b)

        diff.update(cls._diff_functions(old.body, new.body))

        return diff

    @classmethod
    def interesting_functions(cls, klass):
        functions = {
            node.name: node for node in klass

            if isinstance(node, ast.FunctionDef) and
            (is_public(node) or node.name in set(['__init__', '__call__']))
        }

        return functions

    def __repr__(self):
        text = ''

        if self.removed_functions:
            text += 'Removed functions:\n' + repr(self.removed_functions) + '\n'

        if self.added_functions:
            text += 'Added functions:\n' + repr(self.added_functions) + '\n'

        if self.changed_functions:
            text += 'Changed functions:\n'
            for _, function in self.changed_functions.iteritems():
                text += repr(function)

            text += '\n'

        return text


class FunctionDiff(Diff):

    def __init__(self, old, new):
        """Constructor."""

        super(FunctionDiff, self).__init__(old, new)
        ## FIXME: We should allow function names to change, may be...
        assert old.name == new.name
        self.name = old.name

    @classmethod
    def compute_diff(cls, old, new):
        ## FIXME: allow one of old or new to be None.
        diff = {}

        interesting_properties = {
            'arguments': 'args.args',
            'defaults': 'args.defaults',
            'vararg': 'args.vararg',
            'kwarg': 'args.kwarg',
            'decorator_list': 'decorator_list',
        }

        for name, attr in interesting_properties.iteritems():
            a = dotted_getattr(old, attr)
            b = dotted_getattr(new, attr)
            diff[name] = compare(a, b)

        return diff

    def __repr__(self):
        old = '- ' + self._get_signature('old')
        new = '+ ' + self._get_signature('new')
        text = "%s\n%s\n" % (old, new)
        return text

    def _get_signature(self, version):
        assert version in ('old', 'new')
        f = getattr(self, version)

        argnames = [arg.id for arg in f.args.args]
        n = len(argnames)
        d = len(f.args.defaults)

        argnames = [
            name if i < (n - d) else '%s=%s' % (name, f.args.defaults[i-n])
            for i, name in enumerate(argnames)
        ]

        if f.args.vararg is not None:
            argnames.append('*%s' % f.args.vararg)

        if f.args.kwarg is not None:
            argnames.append('**%s' % f.args.kwarg)

        return "def %s(%s)" % (f.name, ', '.join(argnames))


class ModuleDiff(Diff):

    @classmethod
    def compute_diff(cls, old, new):
        return cls._diff_functions(old, new)

    @staticmethod
    def interesting_functions(module):
        functions = {
            node.name: node for node in module
            if isinstance(node, ast.FunctionDef) and is_public(node)
        }

        return functions


    def __repr__(self):
        text = ''

        if self.removed_functions:
            text += 'Removed functions:\n' + repr(self.removed_functions) + '\n'

        if self.added_functions:
            text += 'Added functions:\n' + repr(self.added_functions) + '\n'

        if self.changed_functions:
            text += 'Changed functions:\n'
            for _, function in self.changed_functions.iteritems():
                text += repr(function)

            text += '\n'

        return text


def diff_files(old, new):
    return ModuleDiff(parse_file(old).body, parse_file(new).body)


def diff_functions(old, new):
    return FunctionDiff(old, new)


def diff_classes(old, new):
    return ClassDiff(old, new)


def compare(a, b):
    """ Compare everything under the sun! """

    if type(a) != type(b):
        return (a, b)

    elif isinstance(a, list):
        if len(a) != len(b):
            return (a, b)

        else:
            for i, item in enumerate(a):
                ## FIXME: This function's API is totally unclear... It's
                ## surprising that it kinda works, at all!
                if not compare(item, b[i]):
                    return (a, b)

    elif isinstance(a, ast.Name):
        return a.id == b.id

    elif isinstance(a, ast.Attribute):
        return a.attr == b.attr and a.value.id == b.value.id

    return None
