
import unittest
import logging

from pimpmyclass import mixins, methods, common


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

        @proptype()
        def method3(self, n, t):
            return self.value * n

    return Dummy


class TestMethods(unittest.TestCase):

    def test_timing(self):

        with self.assertRaises(Exception):
            define(methods.StatsMethod)

        Dummy = define(methods.StatsMethod, mixins.StorageMixin)
        x = Dummy()
        y = Dummy()

        def g(i):
            return getattr(i.__class__, 'method')

        self.assertIsNot(g(x).stats, g(y).stats)

        s = g(x).stats(x, 'call')
        self.assertEqual(s.count, 0)

        self.assertEqual(x.method(), 3)

        s = g(x).stats(x, 'call')
        self.assertEqual(s.count, 1)

        s = g(y).stats(y, 'call')
        self.assertEqual(s.count, 0)

    def test_lock(self):

        with self.assertRaises(Exception):
            Dummy = define(methods.LockMethod)

        Dummy = define(methods.LockMethod, mixins.LockMixin)
        x = Dummy()
        self.assertEqual(x.method(), 3)

    def test_async(self):

        Dummy = define(methods.LockMethod, mixins.AsyncMixin)
        Dummy.attach_async(Dummy.method)
        x = Dummy()
        self.assertEqual(x.method(), 3)
        self.assertEqual(x.method_async().result(), 3)

    def test_transformations(self):

        with self.assertRaises(Exception):
            Dummy = define(methods.TransformMethod)

        Dummy = define(methods.TransformMethod, mixins.StorageMixin, mixins.BaseLogMixin)
        x = Dummy()
        self.assertEqual(x.method(), 3)

        self.assertEqual(x.method2(2), 6)

        Dummy.method2.params = {'n': lambda x: 2*x}
        self.assertEqual(x.method2(2), 12)

    def test_transformations_param_ret(self):

        class Dummy(mixins.StorageMixin, mixins.BaseLogMixin):

            @methods.TransformMethod()
            @methods.TransformMethod.param('x', lambda o: 2 * o)
            @methods.TransformMethod.ret(lambda o: o / 9)
            def method(self, x, y):
                return x + y * 3

        d = Dummy()
        self.assertEqual(d.method(2, 3), (2 * 2 + 3 * 3) / 9)

    def test_transformations_param_tuple(self):

        class Dummy(mixins.StorageMixin, mixins.BaseLogMixin):

            @methods.TransformMethod()
            @methods.TransformMethod.param(('x', 'y'), lambda o: 2 * o)
            @methods.TransformMethod.ret(lambda o: o / 9)
            def method(self, x, y):
                return x + y * 3

        d = Dummy()
        self.assertEqual(d.method(2, 3), (2 * 2 + 2 * 3 * 3) / 9)

    def test_transformations1(self):

        class Dummy(mixins.StorageMixin, mixins.BaseLogMixin):

            @methods.TransformMethod(params=lambda o: 3 * o)
            def method(self, x):
                return x * 3

        d = Dummy()
        self.assertEqual(d.method(2), 2 * 3 * 3)

    def test_transformations_deprecated(self):

        with self.assertRaises(Exception):

            class Dummy(mixins.StorageMixin, mixins.BaseLogMixin):

                @methods.TransformMethod(params=lambda o: 3 * o)
                def method(self, x, y):
                    return x + y * 3

    def test_transformations_wrong_name(self):

        with self.assertRaises(Exception):

            class Dummy(mixins.StorageMixin, mixins.BaseLogMixin):

                @methods.TransformMethod()
                @methods.TransformMethod.param('w', lambda o: 2 * o)
                def method(self, x, y):
                    return x + y * 3

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


class TestMethodsConfig(unittest.TestCase):

    def test_config(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config()

        class Dummy:

            @MyMethod(cfg=1)
            def prop(self):
                return None

        self.assertEqual(Dummy.prop._config, dict(cfg=1))
        self.assertEqual(Dummy.prop._kwargs, dict(cfg=1))

    def test_config_missing(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config()

        with self.assertRaises(TypeError):
            class Dummy:

                @MyMethod()
                def prop(self):
                    return None

    def test_config_wrong1(self):

        class MyMethod(methods.NamedMethod):
            pass

        with self.assertRaises(TypeError):
            class Dummy:

                @MyMethod(cfg2=20)
                def prop(self):
                    return None

    def test_config_wrong2(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config()

        with self.assertRaises(TypeError):
            class Dummy:

                @MyMethod(cfg2=20)
                def prop(self):
                    return None

    def test_config_default(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config(default=42)

        class Dummy:

            @MyMethod()
            def prop(self):
                return None

        self.assertEqual(Dummy.prop._config, dict(cfg=42))
        self.assertEqual(dict(Dummy.prop.config_iter(None)), dict(cfg=42))
        self.assertEqual(Dummy.prop._kwargs, {})

    def test_config_default_changed(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config(default=42)

        class Dummy:

            @MyMethod(cfg=43)
            def prop(self):
                return None

        self.assertEqual(Dummy.prop._config, dict(cfg=43))
        self.assertEqual(Dummy.prop._kwargs, dict(cfg=43))

    def test_config_values(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config(valid_values=(True, False))

        class Dummy:

            @MyMethod(cfg=True)
            def prop(self):
                return None

        with self.assertRaises(ValueError):
            class Dummy:

                @MyMethod(cfg=42)
                def prop(self):
                    return None

    def test_config_types(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config(valid_types=(int, ))

        class Dummy:

            @MyMethod(cfg=True)
            def prop(self):
                return None

        with self.assertRaises(TypeError):
            class Dummy:

                @MyMethod(cfg=32.2)
                def prop(self):
                    return None

    def test_config_check_func1(self):

        class MyMethod(methods.NamedMethod):

            cfg = common.Config(check_func=lambda x: x == 32)

        class Dummy:

            @MyMethod(cfg=32)
            def prop(self):
                return None

        with self.assertRaises(ValueError):
            class Dummy:

                @MyMethod(cfg=50)
                def prop(self):
                    return None

    def test_config_check_func2(self):

        def _check(x):
            if x == 32:
                return True
            raise AttributeError

        class MyMethod(methods.NamedMethod):

            cfg = common.Config(check_func=_check)

        class Dummy:

            @MyMethod(cfg=32)
            def prop(self):
                return None

        with self.assertRaises(ValueError):
            class Dummy:

                @MyMethod(cfg=50)
                def prop(self):
                    return None
