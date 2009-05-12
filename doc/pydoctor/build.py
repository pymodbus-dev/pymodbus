#!/usr/bin/env python
from pydoctor.driver import main

#---------------------------------------------------------------------------# 
# A simple runner to build pydoctors documentation
#---------------------------------------------------------------------------# 
if __name__ == "__main__":
    main(
        ["--project-name", "Pymodbus"
         "--project-url",  "http://code.google.com/p/pymodbus/",
         "--add-package",  "../../pymodbus",
         "--html-output",  "pydoctor",
         "--html-write-function-pages", "--quiet", "--make-html"])
