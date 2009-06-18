#!/usr/bin/python
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
        --html --simple-term
        --exclude=._
        --exclude=tests
        --docformat=epytext
        --output=html/
    '''.split()

    if not os.path.exists("./html"): os.mkdir("./html")
    cli()
except: print "Epydoc not avaliable...not building"
