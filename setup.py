#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

def read(filename):
    return open(filename, encoding='utf-8').read()


long_description = '\n\n'.join([read('README.md'),
                                read('AUTHORS'),
                                read('CHANGES')])

setup(
    name='pimpmyclass',
    version='0.4.3',
    description='Pimp your Class/Property/Methods with useful functionality',
    long_description=long_description,
    keywords='classes properties descriptors decorators',
    author='Hernan E. Grecco',
    author_email='hernan.grecco@gmail.com',
    url='https://github.com/hgrecco/pimpmyclass',
    test_suite='pimpmyclass.testsuite.testsuite',
    zip_safe=True,
    packages=['pimpmyclass'],
    include_package_data=True,
    license='BSD',
    python_requires = '>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ])
