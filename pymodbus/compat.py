'''
Python 2.x/3.x Compatibility Layer
-------------------------------------------------

This is mostly based on the jinja2 compat code:

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
'''
import sys
import struct

#---------------------------------------------------------------------------#
# python version checks
#---------------------------------------------------------------------------#
IS_PYTHON2 = sys.version_info[0] == 2
IS_PYTHON3 = sys.version_info[0] == 3
IS_PYPY    = hasattr(sys, 'pypy_translation_info')
IS_JYTHON  = sys.platform.startswith('java')

#---------------------------------------------------------------------------#
# python > 3.3 compatability layer
#---------------------------------------------------------------------------#
if not IS_PYTHON2:
    #-----------------------------------------------------------------------#
    # portable builtins
    #-----------------------------------------------------------------------#
    int2byte     = lambda b: struct.pack('B', b)
    byte2int     = lambda b: b
    unichr       = chr
    range_type   = range
    text_type    = str
    string_types = (str,)
    iterkeys     = lambda d: iter(d.keys())
    itervalues   = lambda d: iter(d.values())
    iteritems    = lambda d: iter(d.items())
    get_next     = lambda x: x.__next__()

    #-----------------------------------------------------------------------#
    # module renames
    #-----------------------------------------------------------------------#
    from io import BytesIO, StringIO
    NativeStringIO = StringIO

    ifilter = filter
    imap = map
    izip = zip
    intern = sys.intern

    import socketserver

    #-----------------------------------------------------------------------#
    # decorators
    #-----------------------------------------------------------------------#
    implements_to_string = lambda x: x

#---------------------------------------------------------------------------#
# python > 2.5 compatability layer
#---------------------------------------------------------------------------#
else:
    #-----------------------------------------------------------------------#
    # portable builtins
    #-----------------------------------------------------------------------#
    int2byte     = chr
    byte2int     = ord
    unichr       = unichr
    text_type    = unicode
    range_type   = xrange
    string_types = (str, unicode)
    iterkeys     = lambda d: d.iterkeys()
    itervalues   = lambda d: d.itervalues()
    iteritems    = lambda d: d.iteritems()
    get_next     = lambda x: x.next()

    #-----------------------------------------------------------------------#
    # module renames
    #-----------------------------------------------------------------------#
    from cStringIO import StringIO as BytesIO, StringIO
    NativeStringIO = BytesIO

    from itertools import imap, izip, ifilter
    intern = intern

    import SocketServer as socketserver

    #-----------------------------------------------------------------------#
    # decorators
    #-----------------------------------------------------------------------#
    def implements_to_string(klass):
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return klass
