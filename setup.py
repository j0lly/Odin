from setuptools import setup, find_packages


setup(
	name='odin',
    version='0.1',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    entry_points = {
        'console_scripts': ['odin=odin.scripts:main'],
    }
)

