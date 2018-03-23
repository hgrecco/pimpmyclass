# -*- coding: utf-8 -*-

import unittest
import logging

from pimpmyclass import mixins, dictprops, props, helpers


class MemHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter(style='{'))
        self.history = list()

    def emit(self, record):
        self.history.append(self.format(record))


def define(proptype, *bases, **kwargs):

    class Dummy(*bases, **kwargs):
        _internal = {}

        @proptype
        def test(self, key):
            return self._internal.get(key, None)

        @test.setter
        def test(self, key, value):
            self._internal[key] = value

    return Dummy


class TestMixins(unittest.TestCase):

    def test_dict(self):

        """
        with self.assertRaises(Exception):
            define(dictprops.DictProperty)
        """

        dummy = define(dictprops.DictProperty)()
        self.assertIsInstance(dummy.test, dictprops.BoundedDictProperty)
        self.assertIs(dummy.test[0], None)
        dummy.test[0] = 4
        self.assertEqual(dummy.test[0], 4)

    def test_dict_cache(self):

        class MyProp(props.PreventUnnecessarySetProperty, props.GetSetCacheProperty):
            pass


        class MyDictProperty(dictprops.DictCacheProperty):

            _subproperty_init = MyProp

        with self.assertRaises(Exception):
            define(dictprops.DictCacheProperty)

        Dummy = define(MyDictProperty, mixins.CacheMixin, mixins.StorageMixin, mixins.BaseLogMixin)

        dummy = Dummy()

        out = dummy.recall('test')
        self.assertEqual(out, {})
        self.assertIsInstance(out, helpers.missingdict)
        # Any non present value
        self.assertEqual(out[1234], Dummy._cache_unset_value)

        self.assertIs(dummy.test[0], None)
        dummy.test[0] = 4

        out = dummy.recall('test')
        self.assertEqual(out, {0: 4})
        self.assertEqual(out[0], 4)
        self.assertIsInstance(out, helpers.missingdict)
        # Any non present value
        self.assertEqual(out[1234], Dummy._cache_unset_value)

        # The storage format is using a (named)tuple
        self.assertEqual(dummy.storage['cache'], {('test', 0): 4})

