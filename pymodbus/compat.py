"""
Python 3.x Compatibility Layer
-------------------------------------------------

This is mostly based on the jinja2 compat code:

    Some py2/py3 compatibility support

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys
import importlib.util
import socketserver
import struct


int2byte = struct.Struct(">B").pack
string_types = str

def iterkeys(d, **kw):
    return iter(d.keys(**kw))

def itervalues(d, **kw):
    return iter(d.values(**kw))

def iteritems(d, **kw):
    return iter(d.items(**kw))

intern = sys

# ----------------------------------------------------------------------- #
# module renames
# ----------------------------------------------------------------------- #
# #609 monkey patch for socket server memory leaks
# Refer https://bugs.python.org/issue37193
socketserver.ThreadingMixIn.daemon_threads = True
# ----------------------------------------------------------------------- #
# decorators
# ----------------------------------------------------------------------- #
byte2int = lambda b: b

def is_installed(module):
    """Check if module is installed."""
    found = importlib.util.find_spec(module)
    return found
