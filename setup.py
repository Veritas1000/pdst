#!/usr/bin/env python3

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup

# Package meta-data.
NAME = 'plextools'
DESCRIPTION = 'Plex Tools'
URL = 'https://gitlab.hulahut.xyz/kevin/plextools'
EMAIL = 'kevin@hulahut.xyz'
AUTHOR = 'Kevin Dion'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = None  # '0.dev1.0'

REQUIRED = [
    'click'  # , 'Pillow', 'fuzzywuzzy', 'python-Levenshtein-wheels', 'numpy', 'scipy',
    # 'simplejson'
]
EXTRAS = {
    'testing': ['parameterized'],
}


here = os.path.abspath(os.path.dirname(__file__))

try:
    with io.open(os.path.join(here, 'readme.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    # packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    # If your package is a single module, use this instead of 'packages':
    py_modules=['plextools'],

    entry_points={
        'console_scripts': ['plextools=plextools.cli:cli'],
    },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    # include_package_data=True,
    license='MIT',
)
