"""setup.

Setup script to generate a python module from the sources.
"""

# -*- coding: utf-8 -*-
# vim: set et ai ts=4 sw=4:
# -------------------------------------------------------------------------
# Copyright (c) 2014, Peter Sommerlad and IFS Institute for Software
# at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or
# modify it under the terms of the license that is included with this
# library/application in the file license.txt.
# -------------------------------------------------------------------------

import os
import sys
from setuptools import setup
import versioneer

if sys.hexversion >= 0x03000000:
    open_file = open
else:
    import codecs
    open_file = codecs.open

PACKAGE = 'SConsider'

try:
    BASEDIR = os.path.dirname(os.path.realpath(__file__))
except NameError:
    BASEDIR = None


def read_file(name):
    """Get the string contained in the file named name."""
    with open_file(name, 'r', encoding='utf-8') as f:
        return f.read()


def get_packages(package):
    """Return root package and all sub-packages."""
    return [
        dirpath for dirpath, _, _ in os.walk(package) if os.path.exists(os.path.join(dirpath, '__init__.py'))
    ]


def get_requirements():
    """Read and parse requirements from file."""
    def read_contents(path, filename):
        requires = []
        with open(os.path.join(path, filename)) as f:
            for req_line in f:
                if req_line.startswith('-r'):
                    requires.extend(read_contents(path, req_line.split()[1]))
                else:
                    requires.append(req_line)
        return requires

    base_path = os.path.dirname(__file__)
    requirements_file_path = os.path.join(base_path, 'requirements.txt')
    return read_contents(base_path, requirements_file_path)


setup(
    name=PACKAGE,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="scons build system extension",
    long_description=read_file(os.path.join(BASEDIR, 'README.adoc')),
    # https://packaging.python.org/specifications/core-metadata/#description-content-type
    long_description_content_type="text/plain; charset=UTF-8",
    # classifier list:
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: POSIX :: SunOS/Solaris",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Build Tools"
    ],
    author="Marcel Huber",
    author_email="marcel.huber@hsr.ch",
    url="https://gitlab.dev.ifs.hsr.ch/ifs/sconsider",
    keywords=['sconsider', 'scons', 'build'],
    license="BSD",
    packages=get_packages(PACKAGE),
    install_requires=get_requirements(),
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'mockito'],
    test_suite='tests',
    include_package_data=True,
    zip_safe=False,
)
