# -*- coding: utf-8 -*-

import unittest
import logging

from pimpmyclass import mixins, props


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

        @proptype()
        def prop(self):
            return 3

        @prop.setter
        def prop(self, value):
            if value is None:
                raise Exception('Arrrg!')

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

            @prop
            def prop(self, value):
                self._value = value

        c = C()
        self.assertEqual(c.prop, c._value)
        c.prop = 3
        self.assertEqual(c._value, 9)
