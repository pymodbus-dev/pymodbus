#!/usr/bin/env python
'''
Installs pymodbus using distutils

Run:
    python setup.py install
to install the package from the source archive.

For information about setuptools
http://peak.telecommunity.com/DevCenter/setuptools#new-and-changed-setup-keywords
'''

from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name = 'pymodbus',
    version = version,
    description = "A fully featured modbus protocol stack in python",
    long_description='''
    Pymodbus aims to be a fully implemented modbus protocol stack implemented
    using twisted.  Its orignal goal was to allow simulation of thousands of
    modbus devices on a single machine for monitoring software testing.
    ''',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications :: GTK',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: System :: Networking',
        'Topic :: Utilities'
    ],
    keywords = 'modbus,twisted',
    author = 'Galen Collins',
    author_email = 'bashwork@gmail.com',
    url='http://code.google.com/p/pymodbus/',
    license = 'LGPL',
    packages = find_packages(exclude=['ez_setup', 'examples', 'tests', 'doc']),
    include_package_data = True,
    zip_safe = True,
    install_requires = [
        'twisted >= 2.5.0',
        'nose >= 0.9.3'
    ],
    test_suite = 'nose.collector',
    entry_points = """
    # -*- Entry points: -*-
    """,
    )
