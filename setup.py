#!/usr/bin/env python3
"""Installs pymodbus using setuptools."""


# --------------------------------------------------------------------------- #
# initialization
# --------------------------------------------------------------------------- #
from setuptools import setup


try:
    from setup_commands import command_classes
except ImportError:
    command_classes = {}


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
