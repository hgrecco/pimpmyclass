Pimp My Class
=============
[![Coverage Status](https://coveralls.io/repos/github/hgrecco/pimpmyclass/badge.svg?branch=master)](https://coveralls.io/github/hgrecco/pimpmyclass?branch=master)
[![Build Status](https://travis-ci.org/hgrecco/pimpmyclass.svg?branch=master)](https://travis-ci.org/hgrecco/pimpmyclass)
![Python Version](https://img.shields.io/pypi/pyversions/pimpmyclass.svg)
[![Python Version](https://img.shields.io/pypi/v/pimpmyclass.svg)](https://pypi.org/project/pimpmyclass/)
[![Documentation Status](https://readthedocs.org/projects/pimpmyclass/badge/?version=latest)](https://pimpmyclass.readthedocs.io/en/latest/?badge=latest)

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

https://github.com/hgrecco/pimpmyclass




