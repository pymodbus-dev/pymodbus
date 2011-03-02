#!/usr/bin/env python
'''
Doxygen API Builder
---------------------
'''
import os, shutil

def is_exe(path):
    ''' Returns if the program is executable
    :param path: The path to the file
    :return: True if it is, False otherwise
    '''
    return os.path.exists(path) and os.access(path, os.X_OK)

def which(program):
    ''' Check to see if an executable exists
    :param program: The program to check for
    :return: The full path of the executable or None if not found
    '''
    fpath, name = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

if which('doxygen') is not None:
    print "Building Doxygen API Documentation"
    os.system("doxygen .doxygen")
    if os.path.exists('../../../build'):
        shutil.move("html", "../../../build/doxygen")
else: print "Doxygen not available...not building"
