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
def preRunner(options):
    ''' Runs the pre testing commands
    @param options The collection of options
    '''
    if options.coverage:
        os.system("rm .coverage")

def mainRunner(options):
    ''' Runs the testing with the supplied options
    @param options The collection of options
    '''
    cmd = "nosetests"
    if options.coverage:
        cmd += " --with-coverage --cover-package=%s" % options.module
        cmd += " --cover-html --cover-html-dir=./doc/coverage/"
    if options.output != "":
        cmd += " 2>&1 > %s" % options.output
    if options.unittest:
        os.system(cmd)

def postRunner(options):
    ''' Runs the post testing commands
    @param options The collection of options
    '''
    if options.coverage:
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
                    dest="output", default="")
    parser.add_option("-u", "--unittest",
                    help="Run nose unit tests",
                    action="store_true", dest="unittest", default=True)
    parser.add_option("-c", "--coverage",
                    help="Run code coverage",
                    action="store_true", dest="coverage", default=False)
    parser.add_option("-m", "--module",
                    help="The module to run coverage tests on",
                    dest="module", default="nose")
    try:
        (opt, arg) = parser.parse_args()

        print "Running Code Coverage Of: %s\n" % opt.module
        preRunner(opt)
        mainRunner(opt)
        postRunner(opt)

    except Exception, ex:
        print ex
        parser.print_help()

#---------------------------------------------------------------------------#
# Main jumper
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    main()
