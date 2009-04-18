#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import media_bundler

setup(
    name='django-media-bundler',
    version=media_bundler.__version__,
    author='Reid Kleckner',
    author_email='rnk@mit.edu',
    description="Django application that bundles your Javascript/CSS, "
               +"and sprites your icons.",
    packages=find_packages(),
    zip_safe=False,
    url='http://github.com/rnk/django-media-bundler/',
    classifiers=[
        "Environment :: Web Environment",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ],
    long_description="",
)
