#!/usr/bin/env python
'''
A simple runner script to run a code coverage run of
a given module
'''

from optparse import OptionParser
import os

#--------------------------------------------------------------------------#
# Helpers
#--------------------------------------------------------------------------#
def runner(module, output):
    cmd = "nosetests --with-coverage --cover-package=%s" % module
    os.system(cmd)
    os.system("rm .coverage")

#--------------------------------------------------------------------------#
# Main Runner
#--------------------------------------------------------------------------#
def main():
    '''
    The main function for this script
    '''
    parser = OptionParser()
    parser.add_option("-o", "--output",
                    help="Where to store coverage results",
                    dest="output", default="coverage.results")
    parser.add_option("-m", "--module",
                    help="The module to run coverage tests on",
                    dest="module", default="nose")
    try:
        (opt, arg) = parser.parse_args()

        print "Running Code Coverage Of: %s\n" % opt.module
        runner(opt.module, opt.output)

    except Exception, ex:
        print ex
        parser.print_help()

#---------------------------------------------------------------------------#
# Main jumper
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    main()
