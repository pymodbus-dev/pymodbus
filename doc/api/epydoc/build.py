#!/usr/bin/env python3
"""Epydoc API Runner.

Using pkg_resources, we attempt to see if epydoc is installed,
if so, we use its cli program to compile the documents
"""
import sys
import os
import shutil
import traceback
import pkg_resources

try:
    pkg_resources.require("epydoc")

    from epydoc.cli import cli  # pylint: disable=import-error
    sys.argv = """epydoc.py pymodbus
        --html --simple-term --quiet
        --include-log
        --graph=all
        --docformat=plaintext
        --debug
        --exclude=._
        --exclude=tests
        --output=html/
    """.split()
    #  bugs in trunk for --docformat=restructuredtext

    if not os.path.exists("./html"):
        os.mkdir("./html")

    print("Building Epydoc API Documentation")
    cli()

    if os.path.exists('../../../build'):
        shutil.move("html", "../../../build/epydoc")
except Exception:  # pylint: disable=broad-except
    traceback.print_exc(file=sys.stdout)
    print("Epydoc not available...not building")
