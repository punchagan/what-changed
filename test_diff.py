import ast
import unittest

from diff import diff_functions


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
        # FIXME: Also have a test for asserting that everything else is None!
        self.assertEqual(2, len(diff.decorator_list))

    def _get_foo(self, args=None, decorator_list=None):
        if decorator_list:
            decorators = '\n'.join('@%s' % deco for deco in decorator_list)

        else:
            decorators = ''

        code = """def foo(%(args)s):\n    return"""
        if args is None:
            args = []
        code = code % {'args': ', '.join(args)}
        code = '%s\n%s' % (decorators, code)

        return ast.parse(code).body[0]

if __name__ == '__main__':
    unittest.main()
