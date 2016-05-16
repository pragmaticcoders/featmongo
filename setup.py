#!/usr/bin/env python
import os
import sys
import re

from setuptools import setup
from setuptools.command.test import test as TestCommand


def read_file(filename):
    """Open and a file, read it and return its contents."""
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path) as f:
        return f.read()


def read_requirements(filename):
    """Open a requirements file and return list of its lines."""
    contents = read_file(filename).strip('\n')
    return contents.split('\n') if contents else []



NAME = 'featmongo'
DESCRIPTION = (
    'Wrapper around pymongo using the serialization '
    'module to convert BSON to python object ')
LONG_DESC = DESCRIPTION
AUTHOR = 'Pragmatic Coders Developers'
AUTHOR_EMAIL = 'dev@pragmaticcoders.com'
LICENSE = "Proprietary"
PLATFORMS = ['any']
REQUIRES = []
SETUP_REQUIRES = ['setuptools>=0.6c9', 'wheel==0.23.0']
INSTALL_REQUIRES = read_requirements('requirements.txt')
TESTS_REQUIRE = read_requirements('requirements_dev.txt')

KEYWORDS = []
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: No Input/Output (Daemon)',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
]


PACKAGES = [
    'featmongo',
]

class PyTest(TestCommand):

    """Command to run unit tests after in-place build."""

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            'tests',
            'featmongo',
        ]
        self.test_suite = True

    def run_tests(self):
        # Importing here, `cause outside the eggs aren't loaded.
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(name = NAME,
      version = '0.3.2',
      description = DESCRIPTION,
      long_description = LONG_DESC,
      author = AUTHOR,
      author_email = AUTHOR_EMAIL,
      license = LICENSE,
      platforms = PLATFORMS,
      setup_requires = SETUP_REQUIRES,
      install_requires = INSTALL_REQUIRES,
      tests_require=TESTS_REQUIRE,
      requires = REQUIRES,
      packages = PACKAGES,
      include_package_data = True,
      keywords = KEYWORDS,
      classifiers = CLASSIFIERS,
      cmdclass={'test': PyTest},
)
