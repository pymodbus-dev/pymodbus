#!/usr/bin/env python3
"""Installs pymodbus using setuptools."""


# --------------------------------------------------------------------------- #
# initialization
# --------------------------------------------------------------------------- #
try:  # if not installed, install and proceed
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
try:
    from setup_commands import command_classes
except ImportError:
    command_classes = {}
from pymodbus import __version__, __author__, __maintainer__

dependencies = {}
with open('requirements.txt') as reqs:
    option = None
    for line in reqs.read().split('\n'):
        if line == '':
            option = None
        elif line.startswith('# install:'):
            option = line.split(':')[1]
            dependencies[option] = []
        elif not line.startswith('#') and option:
            dependencies[option].append(line)

install_req = dependencies['required']
del dependencies['required']


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
setup(
    install_requires=install_req,
    extras_require=dependencies,
    cmdclass=command_classes,
)
