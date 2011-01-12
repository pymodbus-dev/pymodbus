#!/usr/bin/env python
'''
Epydoc API Runner
------------------

Using pkg_resources, we attempt to see if epydoc is installed,
if so, we use its cli program to compile the documents
'''
try:
    import sys, os
    import pkg_resources
    pkg_resources.require("epydoc")

    from epydoc.cli import cli
    sys.argv = '''epydoc.py pymodbus
        --html --simple-term --quiet
        --include-log
        --graph=all
        --docformat=plaintext
        --debug
        --exclude=._
        --exclude=tests
        --output=html/
    '''.split()
    #bugs in trunk for --docformat=restructuredtext

    if not os.path.exists("./html"):
        os.mkdir("./html")
    cli()
    #os.system("mv html ../../../build/epydoc")
except Exception, ex:
    import traceback,sys
    traceback.print_exc(file=sys.stdout)
    print "Epydoc not avaliable...not building"
