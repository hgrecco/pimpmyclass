
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


def guess_indent(text, skip_first=False):
    if not text:
        return ''

    # Find the indentation of this docstring
    # by looking at the minimum number of leading chars
    # in non empty lines

    leading_spaces = 10000000000000
    leading_tabs = 10000000000000

    first_space = False
    first_tab = False

    lines = text.split('\n')

    if skip_first:
        if len(lines) == 1:
            return ''
        lines = lines[1:]

    for line in lines:
        # skip empty lines
        if not line.strip():
            continue
        leading_spaces = min(leading_spaces, len(line) - len(line.lstrip(' ')))
        leading_tabs = min(leading_tabs, len(line) - len(line.lstrip('\t')))

        first_space = first_space or line[0] == ' '
        first_tab = first_tab or line[0] == '\t'

    if first_space and first_tab:
        raise ValueError('Mixed tabs and spaces in docstring\n' + text)
    elif first_space:
        return ' ' * leading_spaces
    elif first_tab:
        return '\t' * leading_tabs
    else:
        return ''


def prepend_to_docstring(s, docstring):
    if not docstring:
        return s

    return guess_indent(docstring, False) + s + docstring


def append_lines_to_docstring(lines, docstring):
    if not docstring:
        return '\n'.join(lines)

    indent = guess_indent(docstring, True)
    out = docstring
    if lines[-1].strip():
        #out += '\n'
        pass
    for line in lines:
        if line:
            out += indent + line + '\n'
        else:
            out += '\n'
    return out + indent


#: This sentinel indicates a configuration value of a property has not been set
#: It is only for internal use as all configurations must have a defined value
#: either by a kwargs during construction or because it has a default value.
CONFIG_UNSET = object()


class Config:

    def __init__(self, valid_values=(), valid_types=(), check_func=None, default=CONFIG_UNSET, doc=''):
        self.__valid_values = valid_values
        self.__valid_types = valid_types
        self.__check_func = check_func
        self.__default = default
        self.__doc__ = doc

    def _check_value(self, value, name):
        if self.__valid_values and value not in self.__valid_values:
            raise ValueError('%r is not a valid value for %s. Should be in %r' %
                             (value, name, self.__valid_values))

        if self.__valid_types and not isinstance(value, self.__valid_types):
            raise TypeError('%r is not a valid type for %s. Should be in %r' %
                            (value, name, self.__valid_types))

        if self.__check_func:
            try:
                ok = self.__check_func(value)
            except Exception as e:
                raise ValueError('The value provided for %s does not pass the check function: %s' % (name, e))
            if not ok:
                raise ValueError('The value provided for %s does not pass the check function')

    def _common(self, owner, name):

        if owner._config_template is None:
            owner._config_template = {name: self.__default}
        else:
            owner._config_template[name] = self.__default

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
        from .props import InstanceConfigurableProperty
        from .methods import InstanceConfigurableMethod
        require_any(self, owner, name, InstanceConfigurableProperty, InstanceConfigurableMethod)

        self._common(owner, name)

        def _iget(selfie, instance):
            return selfie.config_get(instance, name)

        def _iset(selfie, instance, value):
            self._check_value(value, name)
            return selfie.config_set(instance, name, value)

        setattr(owner, name + '_iget', _iget)
        setattr(owner, name + '_iset', _iset)


