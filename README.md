# SConsider

[SConsider][] is a [SCons][] extension to provide a recursive target detection and dependency handling mechanism.

Instead of manually tracking locations of dependent projects and files, [SConsider][] will scan your directory tree for `*.sconsider` files and interpret the setting for building up the _package_ and it's _targets_ during a later phase. To reference a _target_ from another _package_, you can simply reference it like `SomePackage.TargetA`.

[SConsider]: https:/ifs/sconsider
[SCons]: https://scons.org

## Install the development version into your virtualenv

Please check the [packaging][] information to learn more about this topic.

[packaging]: https://packaging.python.org/distributing/#working-in-development-mode

### Install

The following command installs a development version into the current virtualenv:  
`pip install --editable .`  
If you want to omit installing dependencies, add `--no-deps` to the command.

Alternatively you can use the _old style_ command:  
`python setup.py develop`

### Uninstall

To uninstall a previously installed editable version use:  
`pip uninstall sconsider`

In case you used the _old style_ command, you need to use the following command:  
`python setup.py develop --uninstall`

## Running tests

I recommend using [tox][] to execute the tests as it properly sets up the right environment. To see a list of available test environment to execute, list them using `tox -l` and either

  -  run the default environment(s)  
     `tox`
  -  run a specific environment  
     `tox -e some-env`

[tox]: http://tox.testrun.org/

## Create a source/wheel package

The [packaging guide][] will show you how to deploy a package and a short [guide on wheels][] will explain you what wheels are.

[packaging guide]: http://python-packaging-user-guide.readthedocs.org/en/latest/tutorial.html
[guide on wheels]: http://wheel.readthedocs.org/en/latest

Creating a wheel package is also handled by [tox][] and the corresponding environment is `wheel`. It will create the wheel package and if you additionally want to get a source tarball, you can add `sdist` as argument to tox like:  
`tox -e wheel sdist`

## (Test-) Upload to pypi

tbd.

## Overview of available commands

To get an overview of available commands use:

    `python setup.py --help-commands`

Help regarding a specific command can be retrieved using:

    `python setup.py <command> --help`
