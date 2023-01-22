#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='pysch',
    version='0.1',
    description='',
    py_modules=['pysch'],
    package_dir={'pysch': 'pysch'},
    package_data={},
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'pysch = pysch.cli:cli',
        ],
    },
    install_requires=['paramiko', 'pykeepass', 'pyyaml', 'click'],
)
