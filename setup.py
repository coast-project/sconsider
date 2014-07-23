from setuptools import setup, find_packages

setup(
    name="SConsider",
    version="1.5.0",
    packages=find_packages(
        exclude=[
            '*.maintenance',
            'tests']),
    install_requires=[
        'scons >=1.3, <=2.3.0',
        'pyaml',
        'pyopenssl',
        'lepl'],
    package_data={
        '': [
            'license.txt',
            '*.yaml',
            '3rdparty/*/*.sconsider',
            'site_tools/*.sh'],
    },
    dependency_links=[],
    include_package_data=True,
    setup_requires = ['setuptools-git >= 1.0', 'gitegginfo'],
    exclude_package_data = {'': ['.gitignore', '.gitreview', '.project', '.pydevproject'],},
    test_suite='tests',
    tests_require=['nose','mockito'],
    author="Marcel Huber",
    author_email="marcel.huber@hsr.ch",
    license="BSD",
    description="scons build system extension",
    long_description="""\
The main goal/feature of this SCons extension is to provide a recursive target
detection and dependency handling mechanism.
""",
    url="https://redmine.coast-project.org/projects/sconsider",
    # classifier list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
                 "Development Status :: 4 - Beta",
#                 "Development Status :: 5 - Production/Stable",
                 "Environment :: Console",
                 "Intended Audience :: Developers",
                 "License :: OSI Approved :: BSD License",
                 "Natural Language :: English",
                 "Operating System :: MacOS :: MacOS X",
                 "Operating System :: Microsoft :: Windows",
                 "Operating System :: POSIX :: Linux",
                 "Operating System :: POSIX :: SunOS/Solaris",
                 "Programming Language :: Python",
                 "Programming Language :: Python :: 2.7",
                 "Topic :: Software Development :: Build Tools"],
)
