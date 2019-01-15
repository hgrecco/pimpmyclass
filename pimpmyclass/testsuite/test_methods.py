
import unittest
import logging

from pimpmyclass import mixins, methods


class MemHandler(logging.Handler):



    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter(style='{'))
        self.history = list()

    def emit(self, record):
        self.history.append(self.format(record))


def define(proptype, *bases):

    class Dummy(*bases):

        logger_name = 'testing123'

        value = 3

        @proptype()
        def method(self):
            return self.value

        @proptype()
        def method2(self, n):
            return self.value * n

    return Dummy


class TestMethods(unittest.TestCase):

    def test_lock(self):

        with self.assertRaises(Exception):
            Dummy = define(methods.LockMethod)

        Dummy = define(methods.LockMethod, mixins.LockMixin)
        x = Dummy()
        self.assertEqual(x.method(), 3)

    def test_transformations(self):

        with self.assertRaises(Exception):
            Dummy = define(methods.TransformMethod)

        Dummy = define(methods.TransformMethod, mixins.StorageMixin, mixins.BaseLogMixin)
        x = Dummy()
        self.assertEqual(x.method(), 3)

        self.assertEqual(x.method2(2), 6)

        Dummy.method2.params = {'n': lambda x: 2*x}
        self.assertEqual(x.method2(2), 12)

    def test_log(self):

        with self.assertRaises(Exception):
            define(methods.LogMethod)

        Dummy = define(methods.LogMethod, mixins.LogMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.method()
        x.method2(3)

        self.assertEqual(hdl.history, ['Calling method',
                                       'method returned 3',
                                       'Calling method2 with ((3,), {}))',
                                       'method2 returned 9'])

    def test_log_config_false(self):

        Dummy = define(lambda: methods.LogMethod(log_values=False), mixins.LogMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.method()
        x.method2(3)

        self.assertEqual(hdl.history, ['Calling method',
                                       "method returned <class 'int'>",
                                       "Calling method2 with ((<class 'int'>,), {}))",
                                       "method2 returned <class 'int'>"])


    def test_log_config_fun(self):

        Dummy = define(lambda: methods.LogMethod(log_values=lambda x: '%s %s' % (x, type(x))), mixins.LogMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.method()
        x.method2(3)

        self.assertEqual(hdl.history, ['Calling method',
                                       "method returned 3 <class 'int'>",
                                       """Calling method2 with (("3 <class 'int'>",), {}))""",
                                       "method2 returned 9 <class 'int'>"])
