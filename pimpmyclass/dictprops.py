
from .helpers import missingdict, require, DictPropertyNameKey
from .mixins import CacheMixin, ObservableMixin
from .props import NamedProperty


class DictProperty(NamedProperty):

    _subproperties = None
    _subproperty_init = NamedProperty

    def __init__(self, *args, **kwargs):
        self.keys = kwargs.pop('keys', None)
        super().__init__(*args, **kwargs)

        self.kwargs['keys'] = self.keys
        self._subproperties = {}

    def __get__(self, instance, owner=None):

        if instance is None:
            return self

        return BoundedDictProperty(self, instance)

    def __set__(self, instance, value):

        if not isinstance(value, dict):
            raise AttributeError('A dictionary property cannot be set in this way. '
                                 'You probably want to do something like:'
                                 'obj.prop[index] = value or obj.prop = dict')

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


class BoundedDictProperty:
    """Helper class to provide indexed access to DictFeat.
    """

    def __init__(self, dictfeat, instance):
        self.instance = instance
        self.df = dictfeat

    def __getitem__(self, key):

        if self.df.fget is None:
            raise AttributeError('{} is a read-only feat'.format(self.df.name))

        keys = self.df.keys

        if keys and key not in keys:
            raise KeyError('{} is not valid key for {} {}'.format(key, self.df.name, keys))

        if isinstance(keys, dict):
            key = keys[key]

        return DictProperty.getitem(self.df, self.instance, key)

    def __setitem__(self, key, value):

        if self.df.fset is None:
            raise AttributeError('{} is a write-only feat'.format(self.df.name))

        keys = self.df.keys

        if keys and not key in keys:
            raise KeyError('{} is not valid key for {} {}'.format(key, self.df.name, keys))

        if isinstance(keys, dict):
            key = keys[key]

        DictProperty.setitem(self.df, self.instance, key, value)

    def __delete__(self, instance):
        if self.df.fdel:
            raise AttributeError('{} is a permanent feat of {}'.format(self.df.name, instance.__class__.__name__))

    def __repr__(self):
        return repr(self.df.value[self.instance])

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