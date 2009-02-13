'''
Contained is a collection of base classes that are used
throughout the pymodbus library
'''
from zope.interface import Interface, Attribute

#---------------------------------------------------------------------------# 
# Generic
#---------------------------------------------------------------------------# 
class Singleton(object):
	'''
	Singleton base class
	http://mail.python.org/pipermail/python-list/2007-July/450681.html
	'''
	def __new__(cls, *args, **kwargs):
			if '_inst' not in vars(cls):
				cls._inst = object.__new__(cls, *args, **kwargs)
			return cls._inst

#---------------------------------------------------------------------------# 
# Specific
#---------------------------------------------------------------------------# 
class IModbusFramer(Interface):
	'''
	A framer strategy interface. The idea is that we abstract away all the
	detail about how to detect if a current message frame exists, decoding it,
	sending it, etc so that we can plug in a new Framer object (tcp, rtu, ascii)
	'''

	def checkFrame():
		'''
		Check and decode the next frame Return true if we were successful
		'''

	def advanceFrame():
		'''
		This allows us to skip over the current message after we have processed
	   	it or determined that it contains an error. It also has to reset the
		current frame header handle
		'''

	def addToFrame(message):
		'''
		This should be used before the decoding while loop to add the received
		data to the buffer handle.
		@param message The most recent packet
		'''

	def isFrameReady():
		'''
		This is meant to be used in a while loop in the decoding phase to let
		the decoder know that there is still data in the buffer.
		'''

	def getFrame():
		'''
		Return the next frame from the buffered data
		'''

	def populateResult(result):
		'''
		Populates the modbus result with the transport specific header
	   	information (pid, tid, uid, checksum, etc)
		@param result The response packet
		'''

	def buildPacket(message):
		'''
		Creates a ready to send modbus packet from a modbus request/response
		unencoded message.
		@param message The request/response to send
		'''

__all__ = ['Singleton', 'IModbusFramer']
