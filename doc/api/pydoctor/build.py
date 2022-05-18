#!/usr/bin/env python3
"""Pydoctor API Runner.

Using pkg_resources, we attempt to see if pydoctor is installed,
if so, we use its cli program to compile the documents
"""
try:
    import sys
    import os
    import shutil
    import pkg_resources

    pkg_resources.require("pydoctor")

    from pydoctor.driver import main  # pylint: disable=import-error

    sys.argv = """pydoctor.py --quiet
        --project-name=Pymodbus
        --project-url=http://code.google.com/p/pymodbus/
        --add-package=../../../pymodbus
        --html-output=html
        --html-write-function-pages --make-html""".split()

    print("Building Pydoctor API Documentation")
    main(sys.argv[1:])

    if os.path.exists("../../../build"):
        shutil.move("html", "../../../build/pydoctor")
except:  # noqa: E722 NOSONAR pylint: disable=bare-except
    print("Pydoctor unavailable...not building")
