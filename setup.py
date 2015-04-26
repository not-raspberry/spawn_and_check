#!/usr/bin/env python
"""Project setup."""

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

REQUIREMENTS = [
]

TEST_REQUIREMENTS = [
    'pylama==6.3.1',
    'pytest==2.7.0',
]

setup(
    name='spawn_and_check',
    version='0.0.1',
    description="Spawn a process and wait until it's ready. So-called 'Executor'.",
    long_description=README,
    author='Michał Pawłowski',
    author_email='blackmosesorg@gmail.com',
    url='',
    license="MIT",
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    keywords=['executor'],
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    entry_points={},
)
