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

Follow us on GitHub: https://github.com/hgrecco/pimpmyclass

Basic usage
-----------

Pick what capability you need and created your pimped property

.. code-block:: python

   from pimpmyclass import props

   class MyAwesomeProperty(props.StatsProperty):
      """Docs goes here
      """

Check what is required for that class and define your base class
with your properties.

.. code-block:: python

   from pimpmyclass import mixins

   class Base(mixins.StorageMixin):
       """Docs goes here
       """

       @MyAwesomeProperty()
       def just_read(self):
           return 42

       @MyAwesomeProperty()
       def read_write(self):
           return 42

       @read_write.setter
       def read_write(self, value):
           if value != 42:
               raise ValueError

and that's it!

.. code-block:: python

   >>> obj = Base()
   >>> obj.just_read
   42
   >>> obj.just_read
   42
   >>> obj.read_write
   42
   >>> obj.read_write = 42
   >>> obj.read_write = 43
   Traceback (most recent call last):
   ...
   ValueError
   >>> s = Base.just_read.stats(obj, 'get')
   >>> s.count # number of times get was called
   2
   >>> s.last # duration in seconds of the last get call (you can also ask for mean, max, min, std)
   1.414009602740407e-06
   >>> Base.read_write.stats(obj, 'failed_set').count
   1


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
