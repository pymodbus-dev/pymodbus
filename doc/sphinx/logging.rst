===================
Logging in PyModbus
===================

Use the following example as start to enable logging in pymodbus::

    import logging
    
    # Get handles to the various logs
    server_log		= logging.getLogger("pysnmp.server")
    client_log		= logging.getLogger("pysnmp.client")
    protocol_log	= logging.getLogger("pysnmp.protocol")
    store_log		= logging.getLogger("pysnmp.store")

    # Enable logging levels
    server_log.setLevel(logging.DEBUG)
    protocol_log.setLevel(logging.DEBUG)
    client_log.setLevel(logging.DEBUG)
    store_log.setLevel(logging.DEBUG)
    
    # Initialize the logging
    try:
    	logging.basicConfig()
    except Exception, e:
    	print "Logging is not supported on this system"

This can be included in a working project as a separate module
and then used by the rest of the project.
