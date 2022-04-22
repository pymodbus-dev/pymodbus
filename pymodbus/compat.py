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

# --------------------------------------------------------------------------- #
# python version checks
# --------------------------------------------------------------------------- #
PYTHON_VERSION = sys.version_info
IS_PYPY = hasattr(sys, 'pypy_translation_info')
IS_JYTHON = sys.platform.startswith('java')

# --------------------------------------------------------------------------- #
# python > 3.3 compatibility layer
# --------------------------------------------------------------------------- #
# ----------------------------------------------------------------------- #
# portable builtins
# ----------------------------------------------------------------------- #
int2byte = struct.Struct(">B").pack
#NOT USED unichr = six.unichr
#NOT USED range_type = six.moves.range # pylint: disable=invalid-name
#NOT USED text_type = six.string_types
string_types = str

def iterkeys(d, **kw):
    return iter(d.keys(**kw))

def itervalues(d, **kw):
    return iter(d.values(**kw))

def iteritems(d, **kw):
    return iter(d.items(**kw))

def iterlists(d, **kw):
    return iter(d.lists(**kw))

get_next = next
#NOT USED unicode_string = six.u

#NOT USED NativeStringIO = six.StringIO
#NOT USED ifilter = six.moves.filter # pylint: disable=invalid-name
#NOT USED imap = six.moves.map # pylint: disable=invalid-name
izip = zip # pylint: disable=invalid-name
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
implements_to_string = lambda x: x

byte2int = lambda b: b

def is_installed(module):
    """Check if module is installed."""
    found = importlib.util.find_spec(module)
    return found
