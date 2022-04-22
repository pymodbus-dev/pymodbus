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
import struct

# --------------------------------------------------------------------------- #
# python version checks
# --------------------------------------------------------------------------- #
PYTHON_VERSION = sys.version_info

# ----------------------------------------------------------------------- #
# portable builtins
# ----------------------------------------------------------------------- #
int2byte = struct.Struct(">B").pack
string_types = str

# ----------------------------------------------------------------------- #
# decorators
# ----------------------------------------------------------------------- #

byte2int = lambda b: b

def is_installed(module):
    """Check if module is installed."""
    found = importlib.util.find_spec(module)
    return found
