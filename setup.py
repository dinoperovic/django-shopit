#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import sys
import shopit

from setuptools import find_packages, setup


CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
]

setup(
    author='Dino Perovic',
    author_email='dino.perovic@gmail.com',
    name='djangoshop-shopit',
    version=shopit.__version__,
    description='Fully featured shop application built on djangoSHOP framework.',
    long_description_markdown_filename='README.md',
    url='https://github.com/dinoperovic/djangoshop-shopit',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['tests', 'docs']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django-shop>=0.10.0',
        'django-cms>=3.4.2',
        'django-admin-sortable2>=0.6.4',
        'django-measurement>=2.4.0',
        'django-mptt>=0.8.6',
        'django-parler>=1.6.5',
    ],
    setup_requires=['pytest-runner'] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else ['setuptools-markdown'],
    tests_require=['pytest-django'],
)
