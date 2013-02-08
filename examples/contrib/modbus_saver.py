'''
These are a collection of helper methods that can be
used to save a modbus server context to file for backup,
checkpointing, or any other purpose. There use is very
simple::

    context = server.context
    save_json_context('output.json', context)

These can then be re-opened by the parsers in the
modbus_mapping module. At the moment, the supported
output formats are:

* csv
* json
* xml
'''
import csv
import json


def save_json_context(path, context):
    '''

    :param path: The output path for the save file
    :param context: The context to persist to file
    '''
    pass

def save_csv_context(path, context):
    '''

    :param path: The output path for the save file
    :param context: The context to persist to file
    '''
    pass

def save_xml_context(path, context):
    '''

    :param path: The output path for the save file
    :param context: The context to persist to file
    '''
    pass
