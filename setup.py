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
import codecs
from setuptools import setup
from pip.req import parse_requirements
import versioneer

PACKAGE = 'SConsider'

_THISPATH = os.path.abspath(os.path.dirname(__file__))
_README = codecs.open(
    os.path.join(_THISPATH, 'README.md'),
    encoding='utf8').read()
_CHANGES = codecs.open(
    os.path.join(_THISPATH, 'CHANGES.txt'),
    encoding='utf8').read()


def get_packages(package):
    """Return root package and all sub-packages."""
    return [dirpath for dirpath, _, _ in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_requirements():
    """Read and parse requirements from file."""
    requirements_file_path = os.path.join(
        os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_file_path):
        parsed_requirements = parse_requirements(requirements_file_path,
                                                 session=False)
        requirements = [str(ir.req) for ir in parsed_requirements]
    else:
        requirements = []
    return requirements


setup(
    name=PACKAGE,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="scons build system extension",
    long_description=_README + '\n\n' + _CHANGES,
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
    url="https://redmine.coast-project.org/projects/sconsider",
    keywords=['sconsider', 'scons', 'build'],
    license="BSD",
    packages=get_packages(PACKAGE),
    install_requires=get_requirements(),
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'mockito'],
    test_suite='tests',
    include_package_data=True,
    zip_safe=False, )
