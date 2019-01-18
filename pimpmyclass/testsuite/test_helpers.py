

import unittest
import logging

from pimpmyclass import helpers

class TestDoc(unittest.TestCase):

    def assertDocEqual(self, doc1, doc2):
        if doc1 is None or doc2 is None:
            self.assertEqual(doc1, doc2)

        doc1 = '\n'.join(d.strip() for d in doc1.split('\n') if d.strip())
        doc2 = '\n'.join(d.strip() for d in doc2.split('\n') if d.strip())
        self.assertEqual(doc1, doc2)

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

    def test_append_prepend(self):

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

        self.assertDocEqual(helpers.prepend_to_docstring('Async ', f.__doc__), fp.__doc__)
        self.assertDocEqual(helpers.append_lines_to_docstring(['', 'a = 1', 'b = 2'], f.__doc__), fa.__doc__)


