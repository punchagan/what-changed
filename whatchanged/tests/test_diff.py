# Standard library
import unittest

# Local library
from whatchanged.diff import diff_classes, diff_functions
from whatchanged.util import parse_string


class TestFunctionDiff(unittest.TestCase):

    def test_should_detect_equal_functions(self):
        # Given
        foo = self._get_foo()
        bar = self._get_foo()

        # When
        diff = diff_functions(foo, bar)

        # Then
        self.assertIsNone(diff)

    def test_should_detect_change_in_arguments(self):
        # Given
        foo = self._get_foo()
        bar = self._get_foo(['a'])

        # When
        diff = diff_functions(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(2, len(diff.arguments))

    def test_should_detect_change_in_kwarg(self):
        # Given
        foo = self._get_foo()
        bar = self._get_foo(['**kwarg'])

        # When
        diff = diff_functions(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(2, len(diff.kwarg))

    def test_should_detect_change_in_defaults(self):
        # Given
        foo = self._get_foo(['a'])
        bar = self._get_foo(['a=None'])

        # When
        diff = diff_functions(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(2, len(diff.defaults))

    def test_should_detect_change_in_vararg(self):
        # Given
        foo = self._get_foo()
        bar = self._get_foo(['*args'])

        # When
        diff = diff_functions(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(2, len(diff.vararg))

    def test_should_detect_change_in_decorators(self):
        # Given
        foo = self._get_foo(decorator_list=['bar'])
        bar = self._get_foo()

        # When
        diff = diff_functions(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(2, len(diff.decorators))

    def _get_foo(self, args=None, decorator_list=None):
        decorators = '\n'.join('@%s' % deco for deco in decorator_list or [])
        code = """%(decorators)s\ndef foo(%(args)s):\n    return""" % {
            'args': ', '.join(args or []),
            'decorators': decorators
         }

        return parse_string(code).body[0]



class TestClassDiff(unittest.TestCase):

    def test_should_detect_equal_classes(self):
        # Given
        foo = self._get_A()
        bar = self._get_A()

        # When
        diff = diff_classes(foo, bar)

        # Then
        self.assertIsNone(diff)

    def test_should_detect_change_in_bases(self):
        # Given
        foo = self._get_A()
        bar = self._get_A(['a'])

        # When
        diff = diff_classes(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(2, len(diff.bases))

    def test_should_detect_change_in_decorators(self):
        # Given
        foo = self._get_A(decorator_list=['bar'])
        bar = self._get_A()

        # When
        diff = diff_classes(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(2, len(diff.decorators))

    def test_should_detect_change_in_constructor(self):
        # Given
        foo = self._get_A()
        bar = self._get_A_()

        # When
        diff = diff_classes(foo, bar)

        # Then
        self.assertIsNotNone(diff)
        self.assertEqual(1, len(diff.changed_functions))

    def _get_A(self, bases=None, args=None, decorator_list=None):
        if bases is None:
            bases = ['object']
        decorators = '\n'.join('@%s' % deco for deco in decorator_list or [])
        code = """%s\nclass A(%s):\n    pass""" % (decorators, ', '.join(bases))
        return parse_string(code).body[0]

    def _get_A_(self):
        code = """
        class A(object):
            def __init__(self, *args, **kwargs):
                pass
        """
        import textwrap
        code = textwrap.dedent(code)
        return parse_string(code).body[0]

    def _get_method(self, name, args=None, decorator_list=None):
        args = args or ['self']
        decorators = '\n'.join('@%s' % deco for deco in decorator_list or [])
        deco_code = "def %s(): pass"
        extra_code = '\n'.join(deco_code % deco for deco in decorator_list or [])

        code = """%(decorators)s\ndef %(name)s(%(args)s):\n    return""" % {
            'args': ', '.join(args or []),
            'decorators': decorators,
            'name': name
         }
        code = '%s\n%s' % (extra_code, code)

        return code.replace('\n', '\n' + 4 * ' ')


## FIXME: Add tests for module diffs...


if __name__ == '__main__':
    unittest.main()
