#!/usr/bin/env python
'''
This creates a dummy datastore for use with the modbus simulator.

It is also used to convert datastores to and from a register list
dump.  This allows users to build their own data from scratch or
modifiy an exisiting dump.
'''

from pymodbus.datastore import ModbusSequentialDataBlock as seqblock
from pymodbus.datastore import ModbusSparseDataBlock as sparblock
from optparse import OptionParser
import pickle
from sys import exit

#--------------------------------------------------------------------------#
# Helper Classes
#--------------------------------------------------------------------------#
class ConfigurationException(Exception):
    ''' Exception for configuration error '''

    def __init__(self, string):
        '''
        A base string to make pylint happy
        @param string Additional information to append to exception
        '''
        Exception.__init__(self, string)
        self.string = string

    def __str__(self):
        return 'Configuration Error: %s' % self.string

#--------------------------------------------------------------------------#
# Datablock Builders
#--------------------------------------------------------------------------#
def build_translation(option, opt, value, parser):
    '''
    This converts a register dump list to a pickeld datastore
    @param option The option instance
    @param opt The option string specified
    @param value The file to translate
    @param parser The parser object
    '''
    raise ConfigurationException("This function is not implemented yet")
    try:
        stored = open(value, "r")
        data = store.read()
        stored.close()
    except:
        raise ConfigurationException("File Not Found %s" % value)

    stored = open(value + ".trans", "w")
    # TODO
    stored.close()
    exit() # So we don't start a dummy build

def build_conversion(option, opt, value, parser):
    '''
    This converts a pickled datastore to a register dump list
    @param option The option instance
    @param opt The option string specified
    @param value The file to convert
    @param parser The parser object
    '''
    try:
        stored = open(value, "r")
        data = pickle.load(stored)
        stored.close()
    except:
        raise ConfigurationException("File Not Found %s" % value)

    stored = open(value + ".dump", "w")
    for dk,dv in data.iteritems():
        stored.write("[ %s ]\n\n" % dk)

        # handle sequential
        if isinstance(dv.values, list):
            stored.write("\n".join(["[%d] = %d" % (vk,vv)
                    for vk,vv in enumerate(dv.values)]))

        # handle sparse
        elif isinstance(data[k].values, dict):
            stored.write("\n".join(["[%d] = %d" % (vk,vv)
                    for vk,vv in dv.values.iteritems()]))
        else: raise ConfigurationException("Datastore is corrupted %s" % value)
        stored.write("\n\n")
    stored.close()
    exit() # So we don't start a dummy build

#--------------------------------------------------------------------------#
# Datablock Builders
#--------------------------------------------------------------------------#
def build_sequential():
    '''
    This builds a quick mock sequential datastore with 100 values for each
    discrete, coils, holding, and input bits/registers.
    '''
    data = {}
    data['di'] = seqblock(0, [bool(x) for x in range(1, 100)])
    data['ci'] = seqblock(0, [bool(not x) for x in range(1, 100)])
    data['hr'] = seqblock(0, [int(x) for x in range(1, 100)])
    data['ir'] = seqblock(0, [int(2*x) for x in range(1, 100)])
    return data

def build_sparse():
    '''
    This builds a quick mock sparse datastore with 100 values for each
    discrete, coils, holding, and input bits/registers.
    '''
    data = {}
    data['di'] = sparblock([bool(x) for x in range(1, 100)])
    data['ci'] = sparblock([bool(not x) for x in range(1, 100)])
    data['hr'] = sparblock([int(x) for x in range(1, 100)])
    data['ir'] = sparblock([int(2*x) for x in range(1, 100)])
    return data

def main():
    ''' The main function for this script '''
    parser = OptionParser()
    parser.add_option("-o", "--output",
                    help="The output file to write to",
                    dest="file", default="example.store")
    parser.add_option("-t", "--type",
                    help="The type of block to create (sequential,sparse)",
                    dest="type", default="sparse")
    parser.add_option("-c", "--convert",
                    help="Convert a file datastore to a register dump",
                    type="string",
                    action="callback", callback=build_conversion)
    parser.add_option("-r", "--restore",
                    help="Convert a register dump to a file datastore",
                    type="string",
                    action="callback", callback=build_translation)
    try:
        (opt, arg) = parser.parse_args() # so we can catch the csv callback

        if opt.type == "sparse":
            result = build_sparse()
        elif opt.type == "sequential":
            result = build_sequential()
        else:
            raise ConfigurationException("Unknown block type %s" % opt.type)

        output = open(opt.file, "w")
        pickle.dump(result, output)
        output.close()
        print "Created datastore: %s\n" % opt.file

    except ConfigurationException, ex:
        print ex
        parser.print_help()

#---------------------------------------------------------------------------#
# Main jumper
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    main()
