==================================================
Modbus Message Parsing Example
==================================================

This is an example of a parser to decode raw messages
to a readable description. It will attempt to decode
a message to the request and response version of a
message if possible. Here is an example output::

    $./message-parser.py -b -m 000112340006ff076d
    ================================================================================
    Decoding Message 000112340006ff076d
    ================================================================================
    ServerDecoder
    --------------------------------------------------------------------------------
    name            = ReadExceptionStatusRequest
    check           = 0x0
    unit_id         = 0xff
    transaction_id  = 0x1
    protocol_id     = 0x1234
    documentation   = 
        This function code is used to read the contents of eight Exception Status
        outputs in a remote device.  The function provides a simple method for
        accessing this information, because the Exception Output references are
        known (no output reference is needed in the function).
        
    ClientDecoder
    --------------------------------------------------------------------------------
    name            = ReadExceptionStatusResponse
    check           = 0x0
    status          = 0x6d
    unit_id         = 0xff
    transaction_id  = 0x1
    protocol_id     = 0x1234
    documentation   = 
        The normal response contains the status of the eight Exception Status
        outputs. The outputs are packed into one data byte, with one bit
        per output. The status of the lowest output reference is contained
        in the least significant bit of the byte.  The contents of the eight
        Exception Status outputs are device specific.

--------------------------------------------------
Program Source
--------------------------------------------------

.. literalinclude:: ../../../examples/contrib/message-parser.py

--------------------------------------------------
Example Messages
--------------------------------------------------

See the documentation for the message generator
for a collection of messages that can be parsed
by this utility.

