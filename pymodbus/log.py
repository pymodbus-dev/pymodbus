'''
This is a central location for all the system logging

To enable logging, simply import one of the following
logs and set the level you wish to debug at
'''
import logging

server_log		= logging.getLogger("pysnmp.server")
client_log		= logging.getLogger("pysnmp.client")
protocol_log	= logging.getLogger("pysnmp.protocol")
store_log		= logging.getLogger("pysnmp.store")

#---------------------------------------------------------------------------# 
# To set debugging by default, uncomment the following
#---------------------------------------------------------------------------# 
#server_log.setLevel(logging.DEBUG)
#protocol_log.setLevel(logging.DEBUG)
#client_log.setLevel(logging.DEBUG)
#store_log.setLevel(logging.DEBUG)

try:
	logging.basicConfig()
except Exception, e:
	print "Logging is not supported on this system"

__all__ = ['server_log', 'client_log', 'protocol_log', 'store_log']
