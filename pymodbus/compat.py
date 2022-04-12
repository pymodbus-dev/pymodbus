"""
Python 3.x Compatibility Layer
-------------------------------------------------

This is mostly based on the jinja2 compat code:

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys
import importlib.util
import socketserver
import six

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
int2byte = six.int2byte
unichr = six.unichr
range_type = six.moves.range # pylint: disable=invalid-name
text_type = six.string_types
string_types = six.string_types
iterkeys = six.iterkeys
itervalues = six.itervalues
iteritems = six.iteritems
get_next = six.next
unicode_string = six.u

NativeStringIO = six.StringIO
ifilter = six.moves.filter # pylint: disable=invalid-name
imap = six.moves.map # pylint: disable=invalid-name
izip = six.moves.zip # pylint: disable=invalid-name
intern = six.moves.intern

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
