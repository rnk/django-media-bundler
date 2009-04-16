#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='django-media-bundler',
    version="0.1",
    author='Reid Kleckner',
    author_email='rnk@mit.edu',
    description="Django Media Bundler",
    packages=find_packages(),
    zip_safe=False,
    url='',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    long_description="",
)
