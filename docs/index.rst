.. pimpmyclass documentation master file, created by
   sphinx-quickstart on Sat Jan 19 11:14:43 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Pimp My Class
=============
*Pimp your class with awesome features*

This library provides base classes to enable useful behavior in Python Objects.

The central purpose of the library is to extend python properties to allow:

- get/set logging.
- get/set timing, success and failure stats.
- async locking.
- get/set coercion and conversion.
- value cache
- prevent unnecessary set.
- read once properties

But most importantly, it allows owner specific configurations. Properties are
class attributes, and therefore it is difficult to have a property which is, for
exampled cached, in an object but not cached in another instance of the same class.

The library also provides DictProperties: that is properties that can be accessed by key;
and also methods!

Each capability is isolated in individual classes allowing you to pick only what you need.

Basic usage
-----------

Pick
https://github.com/hgrecco/pimpmyclass


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/properties
   api/methods
   api/mixins
   api/dictproperties




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
