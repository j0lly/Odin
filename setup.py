import sys
from pip.req import parse_requirements
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from odin.static import __version__

# from http://stackoverflow.com/questions/14399534/how-can-i-reference-requirements-txt-for-the-install-requires-kwarg-in-setuptool
# FIXME add path discovery or at least an hint because it breaks from tox
#install_reqs = parse_requirements('requirements.txt', session=False)
#requirements = [str(ir.req) for ir in install_reqs]

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
    version=__version__,
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    entry_points = {
        'console_scripts': ['odin=odin.scripts:main'],
    },
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
)

