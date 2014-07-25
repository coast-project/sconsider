
SConsider
=========

SCons extension to provide a recursive target detection and dependency
handling mechanism.

Build a development version
---------------------------

Given the fact that we use git as VCS, we can not use the tag_svn_revision
feature of egg_info. Therefor we make use of the gitegginfo module.

The following command makes use of it and creates the necessary egg-info
directory using the current commit hash appended:

    `python setup.py gitegginfo --tag-git-desc --tag-build .dev develop`

Run tests
---------

Test can either be run the conventional way using the default test framework:

    `python setup.py test`

or by using nose which is a build dependency of the module calling:

    `python setup.py nosetests --with-xunit --where tests/`

The latter is required if you need to get test results in junit xml style to
be analyzed by jenkins for example.

Create a source/wheel package
-----------------------------

For a short packaging guide check this page: http://python-packaging-user-guide.readthedocs.org/en/latest/tutorial.html
For a short tutorial on wheels check this page: http://wheel.readthedocs.org/en/latest/

    `python setup.py bdist_wheel`

To combine source distribution, wheel creation and uploading to PYPI you could use the following command:

    `python setup.py sdist bdist_wheel upload`

Overview of available commands
------------------------------

To get an overview of available commands use:

    `python setup.py --help-commands`

Help regarding a specific command can be retrieved using:

    `python setup.py <command> --help`

