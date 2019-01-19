# -*- coding: utf-8 -*-
"""
    pimpmyclass.helper
    ~~~~~~~~~~~~~~~~~~

    General helper functions and classes.

    :copyright: 2019 by pimpmyclass Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

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


def prepend_to_docstring(s, docstring, mixed_fallback=None):
    if not docstring:
        return s

    try:
        indent = guess_indent(docstring, False)
    except ValueError:
        if mixed_fallback is None:
            raise
        indent = mixed_fallback

    return indent + s + docstring


def append_lines_to_docstring(lines, docstring, mixed_fallback=None):
    if not docstring:
        return '\n'.join(lines)

    try:
        indent = guess_indent(docstring, True)
    except ValueError:
        if mixed_fallback is None:
            raise
        indent = mixed_fallback

    out = docstring

    for line in lines:
        if line:
            out += indent + line + '\n'
        else:
            out += '\n'
    return out + indent

