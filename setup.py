import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand



class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
	name='odin',
    version='0.3',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    entry_points = {
        'console_scripts': ['odin=odin.scripts:main'],
    },
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
)

