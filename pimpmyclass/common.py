# -*- coding: utf-8 -*-
"""
    pimpmyclass.commoon
    ~~~~~~~~~~~~~~~~~~~

    Provides Config, InstanceConfig and a base class for NamedProperties and Methods

    :copyright: 2019 by pimpmyclass Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import inspect

from .helpers import append_lines_to_docstring, require_any


#: This sentinel indicates a configuration value of a property has not been set
#: It is only for internal use as all configurations must have a defined value
#: either by a kwargs during construction or because it has a default value.
CONFIG_UNSET = object()


class Config:

    def __init__(self, valid_values=(), valid_types=(), check_func=None, default=CONFIG_UNSET, doc=''):
        self.valid_values = valid_values
        self.valid_types = valid_types
        self.check_func = check_func
        self.default = default
        self.__doc__ = doc

    def _check_value(self, value, name):
        if self.valid_values and value not in self.valid_values:
            raise ValueError('%r is not a valid value for %s. Should be in %r' %
                             (value, name, self.valid_values))

        if self.valid_types and not isinstance(value, self.valid_types):
            raise TypeError('%r is not a valid type for %s. Should be in %r' %
                            (value, name, self.valid_types))

        if self.check_func:
            try:
                ok = self.check_func(value)
            except Exception as e:
                raise ValueError('The value provided for %s does not pass the check function: %s' % (name, e))
            if not ok:
                raise ValueError('The value provided for %s does not pass the check function')

    def _common(self, owner, name):

        if owner._config_objects is None:
            owner._config_objects = {name: self}
        else:
            owner._config_objects[name] = self

        def _get(selfie):
            return selfie.config_get(None, name)

        def _set(selfie, value):
            self._check_value(value, name)
            return selfie.config_set(None, name, value)

        setattr(owner, name, property(_get, _set))

    def __set_name__(self, owner, name):
        from .props import NamedProperty
        from .methods import NamedMethod
        require_any(self, owner, name, NamedProperty, NamedMethod)

        self._common(owner, name)


class InstanceConfig(Config):

    def __set_name__(self, owner, name):
        # from .props import InstanceConfigurableProperty
        # from .methods import InstanceConfigurableMethod
        # require_any(self, owner, name, InstanceConfigurableProperty, InstanceConfigurableMethod)

        self._common(owner, name)

        def _iget(selfie, instance):
            return selfie.config_get(instance, name)

        def _iset(selfie, instance, value):
            self._check_value(value, name)
            return selfie.config_set(instance, name, value)

        setattr(owner, name + '_iget', _iget)
        setattr(owner, name + '_iset', _iset)


class MetaDoc(type):

    def __new__(cls, name, bases, attrs):
        attrs['_doc'] = attrs.get('__doc__', '')
        return super(MetaDoc, cls).__new__(cls, name, bases, attrs)

    @property
    def __doc__(self):
        return self.fulldoc(self._doc)


class NamedCommon(metaclass=MetaDoc):

    _name = ''
    _kwargs = None

    _config = None
    _config_objects = None

    def __init__(self, **kwargs):

        self._kwargs = {}

        self._config = {}
        for base_class in inspect.getmro(self.__class__):
            if getattr(base_class, '_config_objects', None):
                self._config.update({name: obj.default for name, obj in base_class._config_objects.items()})

        for k in self._config.keys():
            if k in kwargs:
                v = kwargs.pop(k)
                setattr(self, k, v)
                self._kwargs[k] = v

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
        self._name = name

    @classmethod
    def fulldoc(cls, doc):

        if not cls._config_objects:
            return doc

        doc = doc or ''

        lines = ['',
                 '',
                 'Other parameters',
                 '----------------']

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

        lines.append('')

        return append_lines_to_docstring(lines, doc, mixed_fallback='')

    def config_get(self, instance, key):
        return self._config[key]

    def config_set(self, instance, key, value):
        self._config[key] = value

    def config_iter(self, instance):
        for key in self._config.keys():
            yield key, self.config_get(instance, key)

    def on_config_set(self, instance, key, value):
        pass
