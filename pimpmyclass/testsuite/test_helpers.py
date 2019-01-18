

import unittest
import logging

from pimpmyclass import mixins, methods, helpers


class TestDoc(unittest.TestCase):

    def test_indent_spaces(self):
        s4 = "    hello\n    word\n \n    !"
        self.assertEqual(helpers.guess_indent(s4), 4 * ' ')

        s3 = "    hello\n   word\n \n    !"
        self.assertEqual(helpers.guess_indent(s3), 3 * ' ')

    def test_indent_tabs(self):
        s3 = "\t\t\thello\n\t\t\tword\n \n\t\t\t   !"
        self.assertEqual(helpers.guess_indent(s3), 3 * '\t')

        s2 = "\t\thello\n\t\tword\n\n"
        self.assertEqual(helpers.guess_indent(s2), 2 * '\t')

    def test_indent_mixed(self):

        with self.assertRaises(ValueError):
            s3 = "\t\t\thello\n word\n \n\t\t\t   !"
            out = helpers.guess_indent(s3)

    def test_docstring(self):

        def f():
            """This is a function

            And here is the rest
            """

        def fp():
            """Async This is a function

            And here is the rest
            """

        def fa():
            """This is a function

            And here is the rest
            
            a = 1
            b = 2
            """

        print()
        print(repr(helpers.append_lines_to_docstring(['', 'a = 1', 'b = 2'], f.__doc__)))
        print(repr(fa.__doc__))
        self.assertEqual(helpers.prepend_to_docstring('Async ', f.__doc__), fp.__doc__)
        self.assertEqual(helpers.append_lines_to_docstring(['', 'a = 1', 'b = 2'], f.__doc__), fa.__doc__)
