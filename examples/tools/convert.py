#!/usr/bin/env python
"""
This script is used to convert an XML dump to a
serialized ModbusDataStore for use with the simulator.

This is used to convert from the nmodbus datastore xml dump
to our modbus pickled version.
"""
from pymodbus.datastore import ModbusSparseDataBlock as sblock
from optparse import OptionParser
from lxml import etree
import pickle

#--------------------------------------------------------------------------#
# Helper Classes
#--------------------------------------------------------------------------#
class ConversionException(Exception):
    """ Exception for configuration error """

    def __init__(self, string):
        """ Initialize a ConversionException instance

        :param string: Additional information to append to exception
        """
        Exception.__init__(self, string)
        self.string = string

    def __str__(self):
        """ Builds a string representation of the object

        :returns: The string representation of the object
        """
        return 'Conversion Error: %s' % self.string

#--------------------------------------------------------------------------#
# Lxml Parser Tree
#--------------------------------------------------------------------------#
class ModbusXML:
    convert = {
        'true':True,
        'false':False,
    }
    lookup = {
        'InputRegisters':'ir',
        'HoldingRegisters':'hr',
        'CoilDiscretes':'ci',
        'InputDiscretes':'di'
    }

    def __init__(self):
        """
        Initializer for the parser object
        """
        self.next  = 0
        self.result = {'di':{}, 'ci':{}, 'ir':{}, 'hr':{}}

    def start(self, tag, attrib):
        """
        Callback for start node
        @param tag The starting tag found
        @param attrib Attributes dict found in the tag
        """
        if tag == "value":
            try:
                self.next = attrib['index']
            except KeyError: raise ConversionException("Invalid XML: index")
        elif tag in self.lookup:
            self.h = self.result[self.lookup[tag]]

    def end(self, tag):
        """
        Callback for end node
        @param tag The end tag found
        """
        pass

    def data(self, data):
        """
        Callback for node data
        @param data The data for the current node
        """
        if data in self.convert:
            result = self.convert[data]
        else: result = data
        self.h[self.next] = data

    def comment(self, text):
        """
        Callback for node data
        @param data The data for the current node
        """
        pass

    def close(self):
        """
        Callback for node data
        @param data The data for the current node
        """
        return self.result

#--------------------------------------------------------------------------#
# Helper Functions
#--------------------------------------------------------------------------#
def store_dump(result, file):
    """
    Quick function to dump a result to a pickle
    @param result The resulting parsed data
    """
    result['di'] = sblock(result['di'])
    result['ci'] = sblock(result['ci'])
    result['hr'] = sblock(result['hr'])
    result['ir'] = sblock(result['ir'])

    with open(file, "w") as input:
        pickle.dump(result, input)

def main():
    """
    The main function for this script
    """
    parser = OptionParser()
    parser.add_option("-o", "--output",
                    help="The output file to write to",
                    dest="output", default="example.store")
    parser.add_option("-i", "--input",
                    help="File to convert to a datastore",
                    dest="input", default="scrape.xml")
    try:
        (opt, arg) = parser.parse_args()

        parser = etree.XMLParser(target = ModbusXML())
        result = etree.parse(opt.input, parser)
        store_dump(result, opt.output)
        print "Created datastore: %s\n" % opt.output

    except ConversionException, ex:
        print ex
        parser.print_help()

# --------------------------------------------------------------------------- #
# Main jumper
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
