
from collections import UserDict, namedtuple


class DictPropertyNameKey(namedtuple('DictPropertyNameKey', 'name key')):

    def __str__(self):
        return '%s[%r]' % (self.name, self.key)


class missingdict(UserDict):
    """Dictionary that returns UNSET
    """

    __unset_value = None

    def __init__(self, unset_value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__unset_value = unset_value

    def __missing__(self, key):
        return self.__unset_value


def keep_if_not(_skip=None, **kwargs):
    return {k: v for k, v in kwargs.items() if v is not _skip}


def require(inst, owner, name, *parents):
    """Raises a (nicely explained) type error if owner is not a subclass of all parents.

    It is useful when making sure that a certain type of property is only used within
    certain classes.

    Parameters
    ----------
    inst
        instance of a property object or method.
    owner : type
        class of an object.
    name : str
        name of the attribute to which the property object is assigned.
    parents : iterable of type
        classes that owner must inherit.

    Raises
    ------
    TypeError
        If owner does not inherit from all parents.

    """
    for parent in parents:
        if not issubclass(owner, parent):
            raise TypeError('%r is a %r but %r is not a subclass from %r as required' %
                            (name, inst.__class__.__name__, owner.__name__, parent.__name__))


def require_any(inst, owner, name, *parents):
    """Raises a (nicely explained) type error if owner is not a subclass of at least one parent.

    It is useful when making sure that a certain type of property is only used within
    certain classes.

    Parameters
    ----------
    inst
        instance of a property object.
    owner : type
        class of an object.
    name : str
        name of the attribute to which the property object is assigned.
    parents : iterable of type
        classes that owner must inherit at least one.

    Raises
    ------
    TypeError
        If owner does not inherit at least from one parents.

    """
    for parent in parents:
        if issubclass(owner, parent):
            break
    else:
        raise TypeError('%r is a %r but %r is not a subclass from any of %r as required' %
                        (name, inst.__class__.__name__, owner.__name__, parents))


class Config:

    def __set_name__(self, owner, name):
        from .props import InstanceConfigurableProperty
        from .methods import InstanceConfigurableMethod
        require_any(self, owner, name, InstanceConfigurableProperty, InstanceConfigurableMethod)
        if owner._config_keys is None:
            owner._config_keys = set()

        owner._config_keys.add(name)

        def _get(selfie):
            return selfie.config_get(None, name)

        def _set(selfie, value):
            return selfie.config_set(None, name, value)

        def _iget(selfie, instance):
            return selfie.config_get(instance, name)

        def _iset(selfie, instance, value):
            return selfie.config_set(instance, name, value)

        setattr(owner, name, property(_get, _set))
        setattr(owner, name + '_iget', _iget)
        setattr(owner, name + '_iset', _iset)





