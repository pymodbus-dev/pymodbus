"""
Python 2.x/3.x Compatibility Layer
-------------------------------------------------

This is mostly based on the jinja2 compat code:

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys
import six

# --------------------------------------------------------------------------- #
# python version checks
# --------------------------------------------------------------------------- #
PYTHON_VERSION = sys.version_info
IS_PYTHON2 = six.PY2
IS_PYTHON3 = six.PY3
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
range_type = six.moves.range
text_type = six.string_types
string_types = six.string_types
iterkeys = six.iterkeys
itervalues = six.itervalues
iteritems = six.iteritems
get_next = six.next
unicode_string = six.u

NativeStringIO = six.StringIO
ifilter = six.moves.filter
imap = six.moves.map
izip = six.moves.zip
intern = six.moves.intern

if not IS_PYTHON2:
    # ----------------------------------------------------------------------- #
    # module renames
    # ----------------------------------------------------------------------- #
    import socketserver

    # ----------------------------------------------------------------------- #
    # decorators
    # ----------------------------------------------------------------------- #
    implements_to_string = lambda x: x

    byte2int = lambda b: b
    if PYTHON_VERSION >= (3, 4):
        def is_installed(module):
            import importlib.util
            found = importlib.util.find_spec(module)
            return found
    else:
        def is_installed(module):
            import importlib
            found = importlib.find_loader(module)
            return found
# --------------------------------------------------------------------------- #
# python > 2.5 compatability layer
# --------------------------------------------------------------------------- #
else:
    byte2int = six.byte2int
    # ----------------------------------------------------------------------- #
    # module renames

    # ----------------------------------------------------------------------- #
    import SocketServer as socketserver

    # ----------------------------------------------------------------------- #
    # decorators
    # ----------------------------------------------------------------------- #
    def implements_to_string(klass):
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return klass

    def is_installed(module):
        import imp
        try:
            imp.find_module(module)
            return True
        except ImportError:
            return False