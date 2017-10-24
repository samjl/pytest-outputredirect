#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="pytest-outputredirect",
    version='0.2.1',
    author='Sam Lea',
    author_email='samjlea@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['pytest>=2.8.0', "pytest-loglevels>=0.2.0"],
    # the following makes a plugin available to pytest
    entry_points={'pytest11': ['outputredirect = pytest_outputredirect.pytest_outputredirect']},
    # custom PyPI classifier for pytest plugins
    classifiers=["Framework :: Pytest"],
)
