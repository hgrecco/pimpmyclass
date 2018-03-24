
from collections import defaultdict
import functools
import inspect
import weakref

from .helpers import require, Config, keep_if_not
from .mixins import LockMixin, LogMixin, StorageMixin, BaseLogMixin
from .stats import RunningStats


class NamedMethod:

    _func = None

    @property
    def name(self):
        return self._func.__name__

    @property
    def signature(self):
        return inspect.signature(self._func)

    @property
    def parameters(self):
        return tuple(self.signature.parameters.keys())

    def check_signature(self, func):
        pass

    def __set_name__(self, owner, name):
        pass

    def __call__(self, func):
        self.check_signature(func)
        self._func = func

        class NewCallable:

            def __get__(selfie, instance, owner=None):
                if instance is None:
                    return self

                func = functools.partial(self.call, instance)
                func.__wrapped__ = self._func
                return func

            def __name__(self):
                return func.__name__

            def __set_name__(selfie, owner, name):
                self.__set_name__(owner, name)

            def __getattr__(selfie, item):
                return getattr(self, item)

            def __call__(selfie, instance, *args, **kwargs):
                return self._func(instance, *args, **kwargs)

        obj = NewCallable()

        return obj

    def __newcall__(self, instance, *args, **kwargs):
        return self.call(instance, *args, **kwargs)

    def call(self, instance, *args, **kwargs):
        return self._func(instance, *args, **kwargs)

    def raw_call(self, instance, *args, **kwargs):
        return self._func(instance, *args, **kwargs)


class LockMethod(NamedMethod):

    def __set_name__(self, owner, name):
        require(self, owner, name, LockMixin)

        super().__set_name__(owner, name)

    def call(self, instance, *args, **kwargs):
        with instance.lock:
            return super().call(instance, *args, **kwargs)


class LogMethod(NamedMethod):

    def __set_name__(self, owner, name):
        require(self, owner, name, LogMixin)

        super().__set_name__(owner, name)

    def call(self, instance, *args, **kwargs):
        if args or kwargs:
            instance.log_info('Calling %s with (%s, %s))', self.name, args, kwargs)
        else:
            instance.log_info('Calling %s', self.name)

        try:
            out = super().call(instance, *args, **kwargs)
            instance.log_info('%s returned %s', self.name, out)
            return out
        except Exception as e:
            instance.log_error('While calling %s: %s', self.name, e)
            raise e


class StorageMethod(NamedMethod):
    """A property that can store and retrieve information in the instance
    to which is attached.

    Methods and descriptors are class attributes and therefore any attempt to
    naively modify one of their attributes for a single instance of the parent
    class will propagate to all instances. This property overcomes this problem
    by storing information at the instance level.

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


    Requires that the owner class inherits StorageMixin.
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
                             ' as required by StorageMethod' % cls)

        if ns in cls._storage_sub_ns_cls:
            if not issubclass(cls, cls._storage_sub_ns_cls[ns]):
                raise ValueError('Class %r storage namespace (%s) collides with '
                                 'class %r' % (cls, ns, cls._storage_sub_ns_cls[ns]))
        else:
            if cls._storage_ns_init is None:
                raise ValueError('Class %s must specify a storage initializer '
                                 ' as required by StorageMethod' % cls)

            cls._storage_sub_ns_cls[ns] = cls

            # Create partial versions of _store_get and _store_get
            #  with the corresponding namespace
            #  and store it in the specific subclass.
            cls._store_get = functools.partial(cls._ns_store_get, namespace=cls._storage_ns)
            cls._store_set = functools.partial(cls._ns_store_set, namespace=cls._storage_ns)
            cls._store_del = functools.partial(cls._ns_store_del, namespace=cls._storage_ns)

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

        del sto[namespace][self.name]


class StatsMethod(StorageMethod):
    """A property that keep stats on get and set calls.

    Stats can be retrieved with the `stat` methods and
    the following keys:
    - call
    - failed_call

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

    _storage_ns = 'statsm'
    _storage_ns_init = lambda _: defaultdict(RunningStats)

    def __set_name__(self, owner, name):
        require(self, owner, name, LogMixin)
        super().__set_name__(owner, name)

    def call(self, instance, *args, **kwargs):
        with StatsMethod._store_get(self, instance).time('call'):
            return super().call(instance, *args, **kwargs)

    def stats(self, instance, key):
        return StatsMethod._store_get(self, instance).stats(key)


class InstanceConfigurableMethod(StorageMethod):

    _storage_ns = 'iconfigm'
    _storage_ns_init = lambda _: defaultdict(dict)

    _config_keys = None
    _config = None
    _config_unset_value = None

    def __init__(self, *args, **kwargs):
        self._config = {}
        for k in self._config_keys:
            if k in kwargs:
                self._config[k] = kwargs.pop(k)

        super().__init__()

    def config_get(self, instance, key):

        if instance is None:
            return self._config.get(key, self._config_unset_value)
        try:
            return InstanceConfigurableMethod._store_get(self, instance)[key]
        except KeyError:
            return self._config.get(key, None)

    def config_set(self, instance, key, value):
        if instance is None:
            self._config[key] = value
        else:
            InstanceConfigurableMethod._store_get(self, instance)[key] = value

        self.on_config_set(instance, key, value)

    def config_iter(self, instance):
        for key in self._config.keys():
            yield key, self.config_get(instance, key)

    def on_config_set(self, instance, key, value):
        pass


class TransformMethod(InstanceConfigurableMethod):

    _transformations = None
    _storage_ns = 'transformationsm'
    _storage_ns_init = lambda _: defaultdict(dict)

    params = Config()

    def __set_name__(self, owner, name):
        require(self, owner, name, StorageMixin, BaseLogMixin)

        super().__set_name__(owner, name)

        sig = self.signature
        param_names = self.parameters
        if self.params:
            if not isinstance(self.params, dict):
                if len(sig.parameters) > 2:
                    raise ValueError('The syntax for methods with multiple arguments '
                                     'in the constructor has been deprecated. Use the '
                                     'cleaner "param" syntax in %s', name)

                last = param_names[-1]
                self.params = {last: self.params}
        else:
            self.params = {}
            try:
                self.params = dict(self._func.__transform_params__)
                for k in self.__transform_params__.keys():
                    if k not in param_names:
                        raise ValueError('%s is not an argument name of %s', k, name)
                del self._func.__transform_params__
            except AttributeError:
                pass

        assert isinstance(self.params, dict)

    def check_signature(self, func):
        super().check_signature(func)

        if not self.params:
            return

        names = tuple(inspect.signature(func).parameters.keys())

        p = self.params.pop(None, None)

        if not p:
            return

        for name in names[1:]:
            if name not in self.params:
                self.params[name] = p

    def call(self, instance, *args, **kwargs):

        sig = self.signature
        ba = sig.bind(instance, *args, **kwargs)

        t_arg = self.params_iget(instance)
        if t_arg:
            r_arg = t_arg.pop('<ret>', None)
        else:
            r_arg = None
        new_ba = {}

        noop = lambda x: x

        if t_arg:
            
            for param in sig.parameters.values():
                if param.kind != param.POSITIONAL_OR_KEYWORD:
                    raise ValueError('Only named POSITIONAL_OR_KEYWORD arguments are currently '
                                     'supported by transformations.')

            for k, v in ba.arguments.items():
                new_ba[k] = t_arg.get(k, noop)(v)

            ba = sig.bind(**new_ba)
            instance.log_info('<T> Calling %s with (%s, %s)', self.name, ba.args, ba.kwargs)
            try:
                out = super().call(*ba.args, **ba.kwargs)
            except Exception as e:
                instance.log_error('While pre-processing (%s, %s) for %s: %s', ba.args, ba.kwargs, self.name, e)
                raise e
        else:
            out = super().call(*ba.args, **ba.kwargs)

        if r_arg:
            try:
                out = r_arg(out)
            except Exception as e:
                instance.log_error('While post-processing %s for %s: %s', out, self.name, e)
                raise e

        return out

    @classmethod
    def param(cls, names, func):
        """Add modifiers to a specific parameter.

        See Action for more information.
        """
        def decorator(f):
            _param_memo(f, names, func)
            return f
        return decorator

    @classmethod
    def ret(cls, func):
        """Add modifiers to the return value.

        See Action for more information.
        """
        def decorator(f):
            _param_memo(f, '<ret>', func)
            return f
        return decorator


def _param_memo(obj, name, func):
    """Helper function to allow composition of modifiers in a single action.
    """
    if not isinstance(name, str):
        for n in name:
            _param_memo(obj, n, func)
        return

    if not hasattr(obj, '__transform_params__'):
        obj.__transform_params__ = []
    obj.__transform_params__.append((name, func))