#!/usr/bin/env python
"""
Installs pymodbus using distutils

Run:
    python setup.py install
to install the package from the source archive.

For information about setuptools
http://peak.telecommunity.com/DevCenter/setuptools#new-and-changed-setup-keywords
"""

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
from pymodbus.utilities import IS_PYTHON3

CONSOLE_SCRIPTS = [
            'pymodbus.console=pymodbus.repl.client.main:main'
        ]
if IS_PYTHON3:
    CONSOLE_SCRIPTS.append('pymodbus.server=pymodbus.repl.server.main:server')
with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n')
        if (line and not line.startswith('--'))
    ]
    install_requires.append("pyserial >= 3.4")
# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #
setup(
    name="pymodbus",
    version=__version__,
    description="A fully featured modbus protocol stack in python",
    long_description="""
        Pymodbus aims to be a fully implemented modbus protocol stack
        implemented using twisted/asyncio/tornado.
        Its orignal goal was to allow simulation of thousands of modbus devices
        on a single machine for monitoring software testing.
    """,
    classifiers=[
        'Development Status :: 4 - Beta',
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        'Environment :: Console',
        'Environment :: X11 Applications :: GTK',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Networking',
        'Topic :: Utilities'
    ],
    keywords='modbus, twisted, scada',
    author=__author__,
    author_email='bashwork@gmail.com',
    maintainer=__maintainer__,
    maintainer_email='otlasanju@gmail.com',
    url='https://github.com/riptideio/pymodbus/',
    license='BSD-3-Clause',
    packages=find_packages(exclude=['examples', 'test']),
    exclude_package_data={'': ['examples', 'test', 'tools', 'doc']},
    platforms=['Linux', 'Mac OS X', 'Win'],
    include_package_data=True,
    zip_safe=True,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*',
    install_requires=install_requires,
    extras_require={
        'quality': [
            'coverage >= 3.5.3',
            'nose >= 1.2.1',
            'mock >= 1.0.0',
            'pep8 >= 1.3.3'
        ],
        'documents': ['sphinx >= 1.1.3',
                      'sphinx_rtd_theme',
                      'humanfriendly'],
        'twisted': [
            # using platform_python_implementation rather than
            # implementation_name for Python 2 support
            'Twisted[conch,serial]>=20.3.0; platform_python_implementation != "PyPy" or sys_platform != "win32"',
            # pywin32 isn't supported on pypy
            # https://github.com/mhammond/pywin32/issues/1289
            'Twisted[conch]>=20.3.0; platform_python_implementation == "PyPy" and sys_platform == "win32"',
        ],
        'tornado': [
            'tornado == 4.5.3'
        ],

        'repl:python_version <= "2.7"': [
            'click>=7.0',
            'prompt-toolkit==2.0.4',
            'pygments>=2.2.0'
        ],
        'repl:python_version >= "3.6"': [
            'click>=7.0',
            'prompt-toolkit>=3.0.8',
            'pygments>=2.2.0',
            'aiohttp>=3.7.3',
            'pyserial-asyncio>=0.5'
        ]
    },
    entry_points={
        'console_scripts': CONSOLE_SCRIPTS,
    },
    test_suite='nose.collector',
    cmdclass=command_classes,
)

