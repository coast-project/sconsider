import os.path
import codecs
import re

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = codecs.open(os.path.join(here, 'README.txt'), encoding='utf8').read()
CHANGES = codecs.open(
    os.path.join(
        here,
        'CHANGES.txt'),
    encoding='utf8').read()

with codecs.open(os.path.join(os.path.dirname(__file__), 'SConsider', '__init__.py'),
                 encoding='utf8') as version_file:
    metadata = dict(
        re.findall(
            r"""__([a-z]+)__ = "([^"]+)""",
            version_file.read()))

setup(name="SConsider",
      version=metadata['version'],
      description="scons build system extension",
      long_description=README + '\n\n' + CHANGES,
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
          "Topic :: Software Development :: Build Tools"],
      author="Marcel Huber",
      author_email="marcel.huber@hsr.ch",
      url="https://redmine.coast-project.org/projects/sconsider",
      keywords=['sconsider', 'scons', 'build'],
      license="BSD",
      packages=[
          'SConsider',
          'SConsider.site_tools',
          'SConsider.xmlbuilder'],
      install_requires=[
          'scons >=1.3, <=2.3.0',
          'pyaml',
          'pyopenssl',
          'lepl'],
      setup_requires=['gitegginfo', 'flake8'],
      test_suite='tests',
      tests_require=['nose', 'mockito'],
      include_package_data=True,
      zip_safe=False,
      )
