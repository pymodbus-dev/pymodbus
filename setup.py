#!/usr/bin/env python
'''
Installs pymodbus using distutils

Run:
    python setup.py install
to install the package from the source archive.

For information about setuptools
http://peak.telecommunity.com/DevCenter/setuptools#new-and-changed-setup-keywords
'''
try: # if not installed, install and proceed
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from distutils.core import Command
import sys, os

#---------------------------------------------------------------------------# 
# Extra Commands
#---------------------------------------------------------------------------# 
command_classes = {}

class BuildApiDocs(Command):
    ''' Helper command to build the available api documents
    This scans all the subdirectories under api and runs the
    build.py script underneath trying to build the api
    documentation for the given format.
    '''
    user_options = []

    def initialize_options(self):
        ''' options setup '''
        pass

    def finalize_options(self):
        ''' options teardown '''
        pass

    def run(self):
        ''' command runner '''
        old_cwd = os.getcwd()
        for entry in os.listdir('./api'):
            os.chdir('./api/%s' % entry)
            os.system('python build.py')
            os.chdir(old_cwd)

command_classes['build_apidocs'] = BuildApiDocs

#---------------------------------------------------------------------------# 
# Configuration
#---------------------------------------------------------------------------# 
from pymodbus import __version__, __author__

setup(name  = 'pymodbus',
    version = __version__,
    description = "A fully featured modbus protocol stack in python",
    long_description='''
    Pymodbus aims to be a fully implemented modbus protocol stack implemented
    using twisted.  Its orignal goal was to allow simulation of thousands of
    modbus devices on a single machine for monitoring software testing.
    ''',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: X11 Applications :: GTK',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: System :: Networking',
        'Topic :: Utilities'
    ],
    keywords = 'modbus, twisted',
    author = __author__,
    author_email = 'bashwork@gmail.com',
    maintainer = __author__,
    maintainer_email = 'bashwork@gmail.com',
    url='http://code.google.com/p/pymodbus/',
    license = 'BSD',
    packages = find_packages(exclude=['ez_setup', 'examples', 'tests', 'doc']),
    platforms = ["Linux","Mac OS X","Win"],
    include_package_data = True,
    zip_safe = True,
    install_requires = [
        'twisted >= 2.5.0',
        'nose >= 0.9.3',
        'pyserial >= 2.4'
    ],
    test_suite = 'nose.collector',
    cmdclass = command_classes,
)
