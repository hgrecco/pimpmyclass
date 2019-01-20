# -*- coding: utf-8 -*-
"""
    pimpmyclass.dictprops
    ~~~~~~~~~~~~~~~~~~~~~

    DictProperty is a property that behaves like a dictionary.

    Wrapped get methods must have one arguments: key
    Wrapped set methods must have one arguments: key and value

    :copyright: 2019 by pimpmyclass Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import enum

from .helpers import missingdict, require, DictPropertyNameKey
from .mixins import CacheMixin, ObservableMixin
from .props import NamedProperty


class DictProperty(NamedProperty):

    _subproperties = None
    _subproperty_init = NamedProperty

    def __init__(self, *args, **kwargs):
        self.keys = kwargs.pop('keys', None)
        self._subproperties = {}
        super().__init__(*args, **kwargs)

        self._kwargs['keys'] = self.keys


    def __get__(self, instance, owner=None):

        if instance is None:
            return self

        return BoundedDictProperty(self, instance)

    def __set__(self, instance, value):

        if not isinstance(value, dict):
            raise AttributeError('The dictionary property (%s) cannot be set to a type %s '
                                 'You probably want to do something like:'
                                 'obj.prop[index] = value or obj.prop = dict-like' % (self.name, type(value)))

        for key, value in value.items():
            self.setitem(instance, key, value)

    def __delete__(self, instance):
        raise AttributeError('{} is a permanent feat of {}'.format(self.name, instance.__class__.__name__))

    def build_subproperty(self, key, fget, fset, instance=None):
        p = self._subproperty_init(
            fget=fget,
            fset=fset
        )
        return p

    def subproperty(self, instance, key):

        if key not in self._subproperties:
            p = self.build_subproperty(key,
                                       lambda s: self.fget(s, key) if self.fget is not None else None,
                                       lambda s, v: self.fset(s, key, v) if self.fset is not None else None,
                                       instance)
            assert isinstance(p, NamedProperty)
            p.__set_name__(instance.__class__, DictPropertyNameKey(self.name, key))
            self._subproperties[key] = p

        return self._subproperties[key]

    def getitem(self, instance, key):
        return self.subproperty(instance, key).__get__(instance)

    def setitem(self, instance, key, value):
        return self.subproperty(instance, key).__set__(instance, value)

    def delitem(self, instance, key):
        return self.subproperty(instance, key).__delete__(instance)

    def getall(self, instance):
        return {key: self.getitem(instance, key) for key in self._subproperties.keys()}


class BoundedDictProperty:
    """Helper class to provide indexed access to DictFeat.
    """

    def __init__(self, dictfeat, instance):
        self.instance = instance
        self.df = dictfeat

    def _get_key_val(self, key):

        keys = self.df.keys

        if keys is None:
            return key

        if isinstance(keys, enum.EnumMeta):
            if isinstance(key, enum.Enum):
                return key.value

            elif isinstance(key, str):
                try:
                    key = keys[key]
                except KeyError:
                    raise KeyError('{} is not valid key for {} {}'.format(key, self.df.name, keys))

                return key.value

            else:
                raise KeyError('{} is not valid key for {} {}'.format(key, self.df.name, keys))

        elif isinstance(keys, dict):
            try:
                key = keys[key]
            except KeyError:
                raise KeyError('{} is not valid key for {} {}'.format(key, self.df.name, keys))

        elif isinstance(keys, (set, list, tuple)):
            if key not in keys:
                raise KeyError('{} is not valid key for {} {}'.format(key, self.df.name, keys))

        return key

    def __getitem__(self, key):

        if self.df.fget is None:
            raise AttributeError('{} is a read-only feat'.format(self.df.name))

        key = self._get_key_val(key)

        return DictProperty.getitem(self.df, self.instance, key)

    def __setitem__(self, key, value):

        if self.df.fset is None:
            raise AttributeError('{} is a write-only feat'.format(self.df.name))

        key = self._get_key_val(key)

        DictProperty.setitem(self.df, self.instance, key, value)

    def __delete__(self, instance):
        if self.df.fdel:
            raise AttributeError('{} is a permanent feat of {}'.format(self.df.name, instance.__class__.__name__))

    def __repr__(self):
        return '%r.%s[]' % (self.instance, self.df.name)

    def __getattr__(self, item):
        return getattr(self.df, item)


class DictCacheProperty(DictProperty):

    def __set_name__(self, owner, name):
        require(self, owner, name, CacheMixin)

        super().__set_name__(owner, name)

    def recall(self, instance):
        grab = {key: prop.recall(instance) for key, prop in self._subproperties.items()}
        return missingdict(instance._cache_unset_value, grab)

    def store(self, instance, value):
        for name, prop in self._subproperties.items():
            prop.store(instance, value[name])

    def invalidate_cache(self, instance):
        for _, prop in self._subproperties.items():
            prop.invalidate_cache(instance)


class DictObservableProperty(DictCacheProperty):

    def __set_name__(self, owner, name):
        require(self, owner, name, CacheMixin, ObservableMixin)
        setattr(owner, name + '_changed', owner._observer_signal_init())

        super().__set_name__(owner, name)

    # Signals are emitted by subproperties.