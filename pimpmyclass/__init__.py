# -*- coding: utf-8 -*-
"""
    pimpmyclass
    ~~~~~~~~~~~

    Pimp your class with awesome features.

    The central purpose of the library is to extend python properties to allow:

        get/set logging.
        get/set timing, success and failure stats.
        async locking.
        get/set coercion and conversion.
        value cache
        prevent unnecessary set.
        read once properties
        and more ...

    But most importantly, it allows owner specific configurations. Properties are class attributes,
    and therefore it is difficult to have a property which is, for exampled cached, in an object
    but not cached in another instance of the same class.

    The library also provides DictProperties: that is properties that can be accessed by key;
    and also methods!

    Each capability is isolated in individual classes allowing you to pick only what you need.

    These library started by refactoring code from Lantz 0.3 into a reusable and composable module.

    :copyright: 2019 by pimpmyclass Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from . import props, dictprops, methods, mixins
from .common import Config, InstanceConfig

__all__ = ['props', 'dictprops', 'methods', 'mixins', 'Config', 'InstanceConfig']