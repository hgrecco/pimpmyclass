# -*- coding: utf-8 -*-

import unittest
import logging

from pimpmyclass import mixins, props, helpers, common


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

        _internal = 3
        _prop_gs = 8

        @proptype()
        def prop(self):
            return self._internal

        @prop.setter
        def prop(self, value):
            if value is None:
                raise Exception('Arrrg!')

        @proptype()
        def prop_gs(self):
            return self._prop_gs

        @prop_gs.setter
        def prop_gs(self, value):
            self._prop_gs = value

        @proptype()
        def properr(self):
            raise Exception('GetArrrg!')


    return Dummy


class TestNamedProperty(unittest.TestCase):

    def test_name(self):

        Dummy = define(props.NamedProperty)
        self.assertEqual(Dummy.prop.name, 'prop')

    def test_readonly(self):

        class C:

            @props.NamedProperty()
            def prop(self):
                return 4

        o = C()

        self.assertEqual(o.prop, 4)

        with self.assertRaises(AttributeError):
            o.prop = 5

        with self.assertRaises(AttributeError):
            del o.prop

    def test_writeonly(self):

        class C:

            prop = props.NamedProperty()

            _value = 0

            @prop.setter
            def prop(self, value):
                self._value = value

        o = C()

        self.assertEqual(o._value, 0)
        o._value = 4
        self.assertEqual(o._value, 4)

        with self.assertRaises(AttributeError):
            o.prop

        with self.assertRaises(AttributeError):
            del o.prop

    def test_deleteonly(self):

        class C:

            prop = props.NamedProperty()

            _value = 4

            @prop.deleter
            def prop(self):
                self._value = 0

        o = C()

        self.assertEqual(o._value, 4)
        del o.prop
        self.assertEqual(o._value, 0)

        with self.assertRaises(AttributeError):
            o.prop = 4

        with self.assertRaises(AttributeError):
            o.prop

    def test_readwrite_call(self):

        class C:

            _value = 0

            @props.NamedProperty()
            def prop(self):
                return self._value

            @prop
            def prop(self, value):
                self._value = value

        o = C()

        self.assertEqual(o.prop, 0)
        o.prop = 4
        self.assertEqual(o._value, 4)

        with self.assertRaises(AttributeError):
            del o.prop


class TestOtherProperties(unittest.TestCase):

    def test_timing(self):

        with self.assertRaises(Exception):
            define(props.StatsProperty)

        Dummy = define(props.StatsProperty, mixins.StorageMixin)
        x = Dummy()
        y = Dummy()

        def g(i):
            return getattr(i.__class__, 'prop')

        self.assertIsNot(g(x).stats, g(y).stats)

        s = g(x).stats(x, 'get')
        self.assertEqual(s.count, 0)

        self.assertEqual(x.prop, 3)

        s = g(x).stats(x, 'get')
        self.assertEqual(s.count, 1)

        s = g(y).stats(y, 'get')
        self.assertEqual(s.count, 0)

        x.prop = 0
        s = g(x).stats(x, 'set')
        self.assertEqual(s.count, 1)
        s = g(y).stats(y, 'set')
        self.assertEqual(s.count, 0)

        with self.assertRaises(Exception):
            x.prop = None

        s = g(x).stats(x, 'failed_set')
        self.assertEqual(s.count, 1)

    def test_log(self):

        with self.assertRaises(Exception):
            define(props.LogProperty)

        Dummy = define(props.LogProperty, mixins.LogMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.prop = 1
        y = x.prop
        with self.assertRaises(Exception):
            x.prop = None

        with self.assertRaises(Exception):
            x.properr

        self.assertEqual(hdl.history, ['Setting prop to 1',
                                       'prop was set to 1',
                                       'Getting prop',
                                       'Got 3 for prop',
                                       'Setting prop to None',
                                       'While setting prop to None: Arrrg!',
                                       'Getting properr',
                                       'While getting properr: GetArrrg!'])

    def test_log_config_false(self):

        Dummy = define(lambda: props.LogProperty(log_values=False), mixins.LogMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.prop = 1
        y = x.prop
        with self.assertRaises(Exception):
            x.prop = None

        with self.assertRaises(Exception):
            x.properr

        self.assertEqual(hdl.history, ["Setting prop to <class 'int'>",
                                       "prop was set to <class 'int'>",
                                       "Getting prop",
                                       "Got <class 'int'> for prop",
                                       "Setting prop to <class 'NoneType'>",
                                       "While setting prop to <class 'NoneType'>: Arrrg!",
                                       "Getting properr",
                                       "While getting properr: GetArrrg!"])

    def test_derive_log_config_false(self):

        class MyProp(props.LogProperty):
            pass

        Dummy = define(lambda: MyProp(), mixins.LogMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.prop = 1
        y = x.prop
        with self.assertRaises(Exception):
            x.prop = None

        with self.assertRaises(Exception):
            x.properr

        self.assertEqual(hdl.history, ['Setting prop to 1',
                                       'prop was set to 1',
                                       'Getting prop',
                                       'Got 3 for prop',
                                       'Setting prop to None',
                                       'While setting prop to None: Arrrg!',
                                       'Getting properr',
                                       'While getting properr: GetArrrg!'])

    def test_derive_log_config_false(self):

        class MyProp(props.TransformProperty, props.LogProperty):
            pass

        Dummy = define(MyProp, mixins.LogMixin, mixins.StorageMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.prop = 1
        y = x.prop
        with self.assertRaises(Exception):
            x.prop = None

        with self.assertRaises(Exception):
            x.properr

        self.assertEqual(hdl.history, ['Setting prop to 1',
                                       'prop was set to 1',
                                       'Getting prop',
                                       'Got 3 for prop',
                                       'Setting prop to None',
                                       'While setting prop to None: Arrrg!',
                                       'Getting properr',
                                       'While getting properr: GetArrrg!'])

    def test_log_config_fun(self):

        Dummy = define(lambda: props.LogProperty(log_values=lambda x: 2 * x if isinstance(x, int) else x), mixins.LogMixin)
        x = Dummy()

        hdl = MemHandler()
        x.logger.addHandler(hdl)
        x.logger.setLevel(logging.DEBUG)

        x.prop = 1
        y = x.prop
        with self.assertRaises(Exception):
            x.prop = None

        with self.assertRaises(Exception):
            x.properr

        self.assertEqual(hdl.history, ['Setting prop to 2',
                                       'prop was set to 2',
                                       'Getting prop',
                                       'Got 6 for prop',
                                       'Setting prop to None',
                                       'While setting prop to None: Arrrg!',
                                       'Getting properr',
                                       'While getting properr: GetArrrg!'])


    def test_lock(self):

        with self.assertRaises(Exception):
            define(props.LockProperty)

        Dummy = define(props.LockProperty, mixins.LockMixin)
        x = Dummy()

        # TODO better test locks
        x.prop = 3
        x.prop

    def test_transform_get(self):

        with self.assertRaises(Exception):
            define(props.TransformProperty)

        class C(mixins.StorageMixin, mixins.BaseLogMixin):

            _value = 4

            @props.TransformProperty(post_get=lambda x: 2*x)
            def prop(self):
                return self._value

            @prop.setter
            def prop(self, value):
                self._value = value

        c = C()
        self.assertEqual(c.prop, 2*c._value)
        c.prop = 1
        self.assertEqual(c.prop, 2*c._value)

    def test_transform_set(self):

        class C(mixins.StorageMixin, mixins.BaseLogMixin):

            _value = 4

            @props.TransformProperty(pre_set=lambda x: 3*x)
            def prop(self):
                return self._value

            @prop.setter
            def prop(self, value):
                self._value = value

        c = C()
        self.assertEqual(c.prop, c._value)
        c.prop = 3
        self.assertEqual(c._value, 9)

    def test_cache(self):

        # Defaults to False
        Dummy = define(lambda: props.ReadOnceProperty(),
                       mixins.CacheMixin, mixins.BaseLogMixin, mixins.StorageMixin)
        x = Dummy()

        self.assertEqual(x.prop, 3)
        self.assertEqual(x.prop_gs, 8)
        self.assertEqual(x.recall('prop'), 3)
        self.assertEqual(x.recall(('prop', 'prop_gs')), dict(prop=3, prop_gs=8))

    def test_readonce(self):

        # Defaults to False
        Dummy = define(lambda: props.ReadOnceProperty(),
                       mixins.CacheMixin, mixins.BaseLogMixin, mixins.StorageMixin)
        x = Dummy()

        self.assertEqual(x.prop, 3)
        x._internal = 9
        self.assertEqual(x.prop, 9)


    def test_readonce_true(self):
        Dummy = define(lambda: props.ReadOnceProperty(read_once=True),
                       mixins.CacheMixin, mixins.BaseLogMixin, mixins.StorageMixin)
        x = Dummy()

        self.assertEqual(x.prop, 3)
        x._internal = 9
        self.assertEqual(x.prop, 3)

    def test_prevent_unnecesary_set(self):

        # Defaults to False
        Dummy = define(props.PreventUnnecessarySetProperty,
                       mixins.CacheMixin, mixins.BaseLogMixin, mixins.StorageMixin)
        x = Dummy()

        self.assertEqual(x.prop_gs, 8)
        x.prop_gs = 9
        self.assertEqual(x.prop_gs, 9)

        # Because we prevent unnecessary set but we change it under the hood
        # the value is not updated
        x._prop_gs = 0
        x.prop_gs = 9
        self.assertEqual(x.prop_gs, 0)


class TestPropertyConfig(unittest.TestCase):

    def test_config(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config()

        class Dummy:

            @MyProp(cfg=1)
            def prop(self):
                return None

        self.assertEqual(Dummy.prop._config, dict(cfg=1))
        self.assertEqual(Dummy.prop._kwargs, dict(cfg=1))

    def test_config_missing(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config()

        with self.assertRaises(TypeError):
            class Dummy:

                @MyProp()
                def prop(self):
                    return None

    def test_config_wrong1(self):

        class MyProp(props.NamedProperty):
            pass

        with self.assertRaises(TypeError):
            class Dummy:

                @MyProp(cfg2=20)
                def prop(self):
                    return None

    def test_config_wrong2(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config()

        with self.assertRaises(TypeError):
            class Dummy:

                @MyProp(cfg2=20)
                def prop(self):
                    return None

    def test_config_default(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config(default=42)

        class Dummy:

            @MyProp()
            def prop(self):
                return None

        self.assertEqual(Dummy.prop._config, dict(cfg=42))
        self.assertEqual(dict(Dummy.prop.config_iter(None)), dict(cfg=42))
        self.assertEqual(Dummy.prop._kwargs, {})

    def test_config_default_changed(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config(default=42)

        class Dummy:

            @MyProp(cfg=43)
            def prop(self):
                return None

        self.assertEqual(Dummy.prop._config, dict(cfg=43))
        self.assertEqual(Dummy.prop._kwargs, dict(cfg=43))

    def test_config_values(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config(valid_values=(True, False))

        class Dummy:

            @MyProp(cfg=True)
            def prop(self):
                return None

        with self.assertRaises(ValueError):
            class Dummy:

                @MyProp(cfg=42)
                def prop(self):
                    return None

    def test_config_types(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config(valid_types=(int, ))

        class Dummy:

            @MyProp(cfg=True)
            def prop(self):
                return None

        with self.assertRaises(TypeError):
            class Dummy:

                @MyProp(cfg=32.2)
                def prop(self):
                    return None

    def test_config_check_func1(self):

        class MyProp(props.NamedProperty):

            cfg = common.Config(check_func=lambda x: x == 32)

        class Dummy:

            @MyProp(cfg=32)
            def prop(self):
                return None

        with self.assertRaises(ValueError):
            class Dummy:

                @MyProp(cfg=50)
                def prop(self):
                    return None

    def test_config_check_func2(self):

        def _check(x):
            if x == 32:
                return True
            raise AttributeError

        class MyProp(props.NamedProperty):

            cfg = common.Config(check_func=_check)

        class Dummy:

            @MyProp(cfg=32)
            def prop(self):
                return None

        with self.assertRaises(ValueError):
            class Dummy:

                @MyProp(cfg=50)
                def prop(self):
                    return None


class TestDocs(unittest.TestCase):

    def assertDocEqual(self, doc1, doc2):
        if doc1 is None or doc2 is None:
            self.assertEqual(doc1, doc2)

        doc1 = '\n'.join(d.strip() for d in doc1.split('\n') if d.strip())
        doc2 = '\n'.join(d.strip() for d in doc2.split('\n') if d.strip())
        self.assertEqual(doc1, doc2)

    def test_empty(self):

        def correct():
            """
            Other parameters
            ----------------
            cfg
            """

        class MyProp(props.NamedProperty):

            cfg = common.Config()

        self.assertDocEqual(MyProp.__doc__, correct.__doc__)


    def test_non_empty(self):

        def correct():
            """test

            Other parameters
            ----------------
            cfg
            """

        class MyProp(props.NamedProperty):
            """test

            """

            cfg = common.Config()

        self.assertDocEqual(MyProp.__doc__, correct.__doc__)

    def test_default(self):

        def correct():
            """test

            Other parameters
            ----------------
            cfg : (default=1)
            """

        class MyProp(props.NamedProperty):
            """test

            """

            cfg = common.Config(default=1)

        self.assertDocEqual(MyProp.__doc__, correct.__doc__)

    def test_values(self):

        def correct():
            """test

            Other parameters
            ----------------
            cfg : True or False
            """

        class MyProp(props.NamedProperty):
            """test

            """

            cfg = common.Config(valid_values=(True, False))

        self.assertDocEqual(MyProp.__doc__, correct.__doc__)

    def test_types(self):

        def correct():
            """test

            Other parameters
            ----------------
            cfg : int or float
            """

        class MyProp(props.NamedProperty):
            """test

            """

            cfg = common.Config(valid_types=(int, float))

        self.assertDocEqual(MyProp.__doc__, correct.__doc__)

    def test_doc(self):

        def correct():
            """test

            Other parameters
            ----------------
            cfg
                testing 123
            """

        class MyProp(props.NamedProperty):
            """test

            """

            cfg = common.Config(doc='testing 123')

        self.assertDocEqual(MyProp.__doc__, correct.__doc__)

    def test_all(self):

        def correct():
            """test

            Other parameters
            ----------------
            cfg : True or False (default=True)
                testing 123
            """

        class MyProp(props.NamedProperty):
            """test

            """

            cfg = common.Config(valid_values=(True, False), doc='testing 123', default=True)

        self.assertDocEqual(MyProp.__doc__, correct.__doc__)