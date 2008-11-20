'''
Implements a twisted modbus server.

Example run:
	context = ModbusServerContext(d=[0,100], c=[0,100], h=[0,100], i=[0,100])
	reactor.listenTCP(502, ModbusServerFactory(context))
	reactor.run()
'''
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor

from pymodbus.factory import decodeModbusResponsePDU
from pymodbus.factory import decodeModbusRequestPDU
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore import ModbusControlBlock
from pymodbus.datastore import ModbusDeviceIdentification
from pymodbus.transaction import ModbusTCPFramer
from pymodbus.mexceptions import *
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.log import server_log as log

#---------------------------------------------------------------------------#
# Server
#---------------------------------------------------------------------------#
class ModbusProtocol(Protocol):
	''' Implements a modbus server in twisted '''

	def __init__(self):
		''' Initializes server '''
		self.frame = ModbusTCPFramer()

	def connectionMade(self):
		''' Callback for when a client connects '''
		log.debug("Client Connected [%s]" % self.transport.getHost())
		#self.factory.control.counter + 1 ?
	
	def connectionLost(self, reason):
		'''
		Callback for when a client disconnects
		@param reason The client's reason for disconnecting
		'''
		log.debug("Client Disconnected")
		#self.factory.control.counter - 1 ?
	
	def dataReceived(self, data):
		'''
		Callback when we receive any data
		@param data The data sent by the client
		'''
		# if self.factory.control.isListenOnly == False:
		log.debug(" ".join([hex(ord(x)) for x in data]))
		self.frame.addToFrame(data)
		while self.frame.isFrameReady():
			if self.frame.checkFrame():
				result = self.decode(self.frame.getFrame())
				if result is None:
					raise ModbusIOException("Unable to decode response")
				self.frame.populateResult(result)
				self.frame.advanceFrame()
				self.execute(result) # defer?
			else: break

		#while len(data) > 0:
		#	tid, pid, size, uid = struct.unpack('>HHHB', data[0:MBAP_LENGTH])
		#	if size > 1:
		#		result = self.decode(data[MBAP_LENGTH:MBAP_LENGTH + size - 1])
		#		if result is None:
		#			raise ModbusIOException("Unable to decode response")
		#		result.transaction_id = tid
		#		result.protocol_id = pid
		#		result.uint_id = uid
		#		self.execute(result)
		#		data = data[MBAP_LENGTH + size - 1:]
		#	else:
		#		log.debug("Request data too small")
		#		data = []

#---------------------------------------------------------------------------# 
# Extra Helper Functions
#---------------------------------------------------------------------------# 
	def execute(self, request):
		'''
		Executes the request and returns the result
		@param request The decoded request message
		'''
		try:
			response = request.execute(self.factory.store)
		except:
			log.debug("Datastore unable to fulfill request")
			response = request.doException(merror.SlaveFailure)
		response.transaction_id = request.transaction_id
		response.uint_id = request.unit_id
		self.send(response)

	def send(self, message):
		'''
		Send a request (string) to the network
		@param message The unencoded modbus response
		'''
		return self.transport.write(self.frame.buildPacket(message))

	def decode(self, message):
		'''
		Decodes a request packet
		@param message The raw modbus request packet
		'''
		try:
			return decodeModbusRequestPDU(message)
		except ModbusException, er:
			log.warn("Unable to decode request")
		return None


class ModbusServerFactory(ServerFactory):
	'''
	Builder class for a modbus server

	This also holds the server datastore so that it is
	persisted between connections
	'''

	protocol = ModbusProtocol
	
	def __init__(self, store, identity=None):
		'''
		Overloaded initializer for the modbus factory
		@param store The ModbusServerContext datastore
		@param identity An optional identify structure

		If the identify structure is not passed in, the ModbusControlBlock
		uses its own empty structure.
		'''
		if isinstance(store, ModbusServerContext):
			self.store = store
		else: self.store = ModbusServerContext()
		self.control = ModbusControlBlock()

		if isinstance(identity, ModbusDeviceIdentification):
			self.control.Identity = identity

