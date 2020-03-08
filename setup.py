#!/usr/bin/env python3
import os
from setuptools import setup, find_packages


with open('mutil/version.py') as f:
    exec(f.read())


setup(
    name='mutil',
    author='n4sr',
    version=__version__,
    url='https://github.com/n4sr/mutil',
    license='GPL3',
    packages=find_packages(),
    install_requires=['tinytag>=1.2.2'],
    python_requires='>=3.6',
    entry_points={'console_scripts': ['mutil=mutil.__main__:main']}
)