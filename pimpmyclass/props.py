

from collections import defaultdict
import functools as ft
import inspect
import weakref

from .helpers import missingdict, require, DictPropertyNameKey, InstanceConfig, CONFIG_UNSET, append_lines_to_docstring
from .stats import RunningStats
from .mixins import StorageMixin, BaseLogMixin, LockMixin, CacheMixin, ObservableMixin


class NamedProperty:
    """A property that takes the name of the class attribute to which it is assigned.

    The name must be convertible to string.
    """

    name = ''
    kwargs = None

    _config = None
    _config_objects = None

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, **kwargs):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            self.__doc__ = fget.__doc__
        elif doc is not None:
            self.__doc__ = doc

        self.kwargs = {}

        self._config = {name: obj.default for name, obj in self._config_objects.items()}
        if self._config:
            for k in self._config.keys():
                if k in kwargs:
                    v = kwargs.pop(k)
                    setattr(self, k, v)
                    self.kwargs[k] = v

        if kwargs:
            raise TypeError("%s() got an unexpected keyword argument '%s'" %
                            (self.__class__.__name__, list(kwargs.keys())[0]))

        if self._config:
            missing = tuple(k for k, v in self._config.items() if v is CONFIG_UNSET)
            if missing:
                raise TypeError("%s() is missing %d positional argument%s: %s" %
                                (self.__class__.__name__, len(missing),
                                 's' if len(missing) > 1 else '', ','.join(missing)))

    def __set_name__(self, owner, name):
        self.name = name

    @classmethod
    def fulldoc(cls):
        if not cls._config_objects:
            return cls.__doc__

        doc = cls.__doc__ or ''

        lines = ['Inherited parameters',
                 '--------------------']

        for name, obj in cls._config_objects.items():
            desc = []
            if obj.valid_values:
                desc.append(' or '.join(repr(el) for el in obj.valid_values))
            if obj.valid_types:
                desc.append(' or '.join(el.__name__ for el in obj.valid_types))
            if obj.check_func:
                desc.append(' Note: checking function')

            if desc:
                desc = ' and '.join(desc)
            else:
                desc = ''
            if obj.default is not CONFIG_UNSET:
                if desc:
                    desc += ' '
                desc += '(default=%r)' % obj.default

            if desc:
                lines.append('%s : %s' % (name, desc))
            else:
                lines.append(name)

            if obj.__doc__:
                lines.append('    ' + obj.__doc__)

        return append_lines_to_docstring(lines, doc, mixed_fallback='')

    def __call__(self, func):
        if self.fget is None:
            return self.getter(func)

        return self.setter(func)

    def __get__(self, instance, objtype=None):
        if instance is None:
            return self

        if self.fget is None:
            raise AttributeError('%s is a read-only property of %s' %
                                 (self.name, instance.__class__.__name__))

        return self.get(instance, objtype)

    def __set__(self, instance, value):

        if self.fset is None:
            raise AttributeError('%s is a write-only property of %s' %
                                 (self.name, instance.__class__.__name__))

        self.set(instance, value)

    def __delete__(self, instance):

        if self.fdel is None:
            raise AttributeError('%s is a permanent feat of %s' %
                                 (self.name, instance.__class__.__name__))

        self.delete(instance)

    @property
    def fget_signature(self):
        return inspect.signature(self.fget)

    def get(self, instance, objtype):
        return self.fget(instance)

    def set(self, instance, value):
        return self.fset(instance, value)

    def delete(self, instance):
        return self.fdel(instance)

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.doc,
                          **getattr(self, 'kwargs') or {})

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.doc,
                          **getattr(self, 'kwargs') or {})

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.doc,
                          **getattr(self, 'kwargs') or {})

    def config_get(self, instance, key):
        return self._config[key]

    def config_set(self, instance, key, value):
        self._config[key] = value

    def config_iter(self, instance):
        for key in self._config.keys():
            yield key, self.config_get(instance, key)

    def on_config_set(self, instance, key, value):
        pass


class StorageProperty(NamedProperty):
    """A property that can store and retrieve information in the instance
    to which is attached.

    Requires that the owner class inherits StorageMixin.

    Notes
    -----

    The information is stored in uniquely a specified namespace defined by
    the derived class. Inside that storage, another namespace is specified
    using the property name.

    Derived class should use the dynamically created _store_get and _store_set
    to retrieve and store information.

    Derived classes must override the following variables:

    _storage_ns : str
        Defines a unique namespace under which the information of the
        derived class is stored.

    _storage_ns_init : callable
        Called upon initialization of the storage to initialize the
        specific storage of the namespace.

    """

    # Stores namespace to StorageProperty subclass
    # It cannot be dunder because it is accessed by __init_subclass__
    _storage_sub_ns_cls = weakref.WeakValueDictionary()

    _storage_ns = ''
    _storage_ns_init = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        ns = cls._storage_ns
        if not ns:
            raise ValueError('Class %s must specify a storage namespace '
                             ' as required by StorageProperty' % cls)

        if ns in cls._storage_sub_ns_cls:
            if not issubclass(cls, cls._storage_sub_ns_cls[ns]):
                raise ValueError('Class %r storage namespace (%s) collides with '
                                 'class %r' % (cls, ns, cls._storage_sub_ns_cls[ns]))
        else:
            if cls._storage_ns_init is None:
                raise ValueError('Class %s must specify a storage initializer '
                                 ' as required by StorageProperty' % cls)

            cls._storage_sub_ns_cls[ns] = cls

            # Create partial versions of _store_get and _store_get
            #  with the corresponding namespace
            #  and store it in the specific subclass.
            cls._store_get = ft.partial(cls._ns_store_get, namespace=cls._storage_ns)
            cls._store_set = ft.partial(cls._ns_store_set, namespace=cls._storage_ns)
            cls._store_del = ft.partial(cls._ns_store_del, namespace=cls._storage_ns)

    def __set_name__(self, owner, name):
        require(self, owner, name, StorageMixin)

        super().__set_name__(owner, name)

    def _store_get(self, instance):
        return self._ns_store_get(instance, self._storage_ns)

    def _store_set(self, instance, value):
        return self._ns_store_set(instance, value, self._storage_ns)

    def _store_del(self, instance):
        return self._ns_store_del(instance, self._storage_ns)

    def _ns_store_get(self, instance, namespace):
        sto = instance.storage

        if namespace not in sto:
            cls = self._storage_sub_ns_cls[namespace]
            sto[namespace] = cls._storage_ns_init(instance)

        return sto[namespace][self.name]

    def _ns_store_set(self, instance, value, namespace):
        sto = instance.storage

        if namespace not in sto:
            cls = self._storage_sub_ns_cls[namespace]
            sto[namespace] = cls._storage_ns_init(instance)

        sto[namespace][self.name] = value

    def _ns_store_del(self, instance, namespace):
        sto = instance.storage

        if namespace not in sto:
            cls = self._storage_sub_ns_cls[namespace]
            sto[namespace] = cls._storage_ns_init(instance)

        try:
            del sto[namespace][self.name]
        except KeyError:
            pass


class StatsProperty(StorageProperty):
    """A property that keep stats on get and set calls.

    Stats can be retrieved with the `stat` methods and
    the following keys:
    - get
    - set
    - failed_get
    - failed_set

    The following statistics are provided in a namedtuple
    last : float
        most recent duration (seconds).
    count : int
        number of operations.
    mean : float
        average duration per operation (seconds).
    std : float
        standard deviation of the duration (seconds).
    min : float
        shortest duration (seconds).
    max : float
        longest duration (seconds).


    Requires that the owner class inherits StorageMixin.
    """

    _storage_ns = 'stats'
    _storage_ns_init = lambda _: defaultdict(RunningStats)

    def get(self, instance, objtype):

        with StatsProperty._store_get(self, instance).time('get'):
            return super().get(instance, objtype)

    def set(self, instance, value):

        with StatsProperty._store_get(self, instance).time('set'):
            return super().set(instance, value)

    def stats(self, instance, key):
        return StatsProperty._store_get(self, instance).stats(key)


class LogProperty(NamedProperty):
    """A property that log operations.

    Requires that the owner class inherits LogMixin.
    """

    log_values = True

    def __init__(self, *args, **kwargs):
        self.log_values = kwargs.pop('log_values', True)
        super().__init__(*args, **kwargs)

        self.kwargs.update({'log_values': self.log_values})

    def __set_name__(self, owner, name):
        require(self, owner, name, BaseLogMixin)

        super().__set_name__(owner, name)

    def _to_log(self, instance, value):
        if self.log_values is True:
            return value

        elif callable(self.log_values):
            try:
                return self.log_values(value)
            except Exception as e:
                instance.log_error('Could not convert value to log in %s, logging type: e', self.name, e)

        return type(value)

    def get(self, instance, objtype):

        instance.log_info('Getting %s', self.name)
        try:
            value = super().get(instance, objtype)
            log_value = self._to_log(instance, value)
            instance.log_debug('Got %s for %s', log_value, self.name)
        except Exception as e:
            instance.log_error('While getting %s: %s', self.name, e)
            raise e

        return value

    def set(self, instance, value):
        log_value = self._to_log(instance, value)
        instance.log_debug('Setting %s to %s', self.name, log_value)
        try:
            super().set(instance, value)
            instance.log_debug('%s was set to %s', self.name, log_value)
        except Exception as e:
            instance.log_error('While setting %s to %s: %s', self.name, log_value, e)
            raise e


class LockProperty(NamedProperty):
    """A property that with a set or get Lock.

    Requires that the owner class inherits LogMixin.
    """

    def __set_name__(self, owner, name):
        require(self, owner, name, LockMixin)

        super().__set_name__(owner, name)

    def get(self, instance, objtype):

        with instance.lock:
            return super().get(instance, objtype)

    def set(self, instance, value):
        with instance.lock:
            return super().set(instance, value)


class InstanceConfigurableProperty(StorageProperty):
    """A property that contains owner instance specific configuration variable.

    Requires that the owner class inherits StorageMixin.
    """

    _storage_ns = 'iconfig'
    _storage_ns_init = lambda _: defaultdict(dict)

    def config_get(self, instance, key):

        if instance is None:
            return super().config_get(None, key)

        try:
            return InstanceConfigurableProperty._store_get(self, instance)[key]
        except KeyError:
            return super().config_get(None, key)

    def config_set(self, instance, key, value):
        if instance is None:
            super().config_set(None, key, value)
        else:
            InstanceConfigurableProperty._store_get(self, instance)[key] = value

        self.on_config_set(instance, key, value)


class TransformProperty(InstanceConfigurableProperty):
    """A property that can transform value before a set operation
    or after a get operation.

    Requires that the owner class inherits InstanceConfigurableProperty.
    """

    pre_set = InstanceConfig(default=None, check_func=lambda x: x is None or callable(x))
    post_get = InstanceConfig(default=None, check_func=lambda x: x is None or callable(x))

    def __set_name__(self, owner, name):
        require(self, owner, name, StorageMixin, BaseLogMixin)

        super().__set_name__(owner, name)

    def get(self, instance, objtype):

        value = super().get(instance, objtype)

        transform = self.post_get_iget(instance)

        if not transform:
            return value

        try:
            value = transform(value)
            instance.log_debug('<T> Got %s for %s', value, self.name)
            return value
        except Exception as e:
            instance.log_error('While post-processing %s for %s: %s', value, self.name, e)
            raise e

    def set(self, instance, value):

        transform = self.pre_set_iget(instance)

        if transform:

            try:
                value = transform(value)
                instance.log_info('<T> Setting %s = %s', self.name, value)
            except Exception as e:
                instance.log_error('While pre-processing %s for %s: %s', value, self.name, e)
                raise e

        super().set(instance, value)


class CacheProperty(StorageProperty):
    """A property that can store, recall or invalidate a cache.
    """

    _storage_ns = 'cache'
    _storage_ns_init = lambda instance: missingdict(instance._cache_unset_value)

    def __set_name__(self, owner, name):
        require(self, owner, name, CacheMixin, BaseLogMixin)

        super().__set_name__(owner, name)

    def recall(self, instance):
        return CacheProperty._store_get(self, instance)

    def store(self, instance, value):
        CacheProperty._store_set(self, instance, value)

    def invalidate_cache(self, instance):
        CacheProperty._store_del(self, instance)


class GetCacheProperty(CacheProperty):
    """A property that stores the get value in the cache.

    Requires that the owner class inherits StorageMixin.
    """

    def get(self, instance, objtype):

        value = super().get(instance, objtype)

        self.store(instance, value)

        return value


class SetCacheProperty(CacheProperty):
    """A property that stores the set value in the cache.

    Requires that the owner class inherits StorageMixin.
    """

    def set(self, instance, value):
        super().set(instance, value)

        self.store(instance, value)


class GetSetCacheProperty(GetCacheProperty, SetCacheProperty):
    """A property that stores the get or set value in the cache.

    Requires that the owner class inherits StorageMixin.
    """


class PreventUnnecessarySetProperty(SetCacheProperty):
    """A property that prevents unnecessary set operations by comparing
    the value in the cache with the value to be set.

    Requires that the owner class inherits CacheMixin and LogMixin.
    """

    def set(self, instance, value):
        current_value = self.recall(instance)

        if value == current_value:
            instance.log_info('No need to set %s = %s (current=%s)', self.name, value, current_value)
            return

        super().set(instance, value)

    def force_set(self, instance, value):
        self.invalidate_cache(instance)
        self.set(instance, value)


class ReadOnceProperty(InstanceConfigurableProperty, GetCacheProperty):

    read_once = InstanceConfig(default=False, valid_types=(bool, ))

    def get(self, instance, owner=None):
        if self.read_once_iget(instance) and self.recall(instance) is not instance._cache_unset_value:
            return self.recall(instance)

        return super().get(instance, owner)


class ObservableProperty(CacheProperty):
    """A property that emits a signal when the cached value is changed
    (either via set or get)
    """

    def __set_name__(self, owner, name):
        if isinstance(name, str):
            require(self, owner, name, CacheMixin, ObservableMixin)
            setattr(owner, name + '_changed', owner._observer_signal_init())

        super().__set_name__(owner, name)

    def store(self, instance, value):
        if isinstance(self.name, DictPropertyNameKey):
            old_value = self.recall(instance)
            super().store(instance, value)
            getattr(instance, self.name.name + '_changed').emit(value, old_value, self.name.key)
        else:
            old_value = self.recall(instance)
            super().store(instance, value)
            getattr(instance, self.name + '_changed').emit(value, old_value)
