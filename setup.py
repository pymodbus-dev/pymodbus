#!/usr/bin/env python3
"""Installs pymodbus using setuptools."""


# --------------------------------------------------------------------------- #
# initialization
# --------------------------------------------------------------------------- #
from setuptools import setup


dependencies: dict = {}
with open("requirements.txt") as reqs:
    option = None
    for line in reqs.read().split("\n"):
        if not line:
            option = None
        elif line.startswith("# install:"):
            option = line.split(":")[1]
            dependencies[option] = []
        elif not line.startswith("#") and option:
            dependencies[option].append(line)

install_req = dependencies["required"]
del dependencies["required"]


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
setup(
    install_requires=install_req,
    extras_require=dependencies,
    package_data={
        "pymodbus": ["py.typed", "server/simulator/setup.json", "server/simulator/web/**/*"],
    },
)
