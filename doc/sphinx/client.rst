=================================
Implementation of a Modbus Client
=================================

This attempts to fire off requets in succession so as to work as fast as
possible, but still refrain from overloading the remote device (usually
very mediocre in hardware)

Example Run::

	def clientTest():
		requests = [ ReadCoilsRequest(0,99) ]
		p = reactor.connectTCP("localhost", 502, ModbusClientFactory(requests))
	
	if __name__ == "__main__":
		reactor.callLater(1, clientTest)
		reactor.run()

What follows is a quick layout of the client logic:
 1. Build request array and instantiate a client factory
 2. Defer it until the reactor is running
 3. Upon connection, instantiate the producer and pass it:

   * A handle to the transport
   * A handle to the request array
   * A handle to a sent request handler
   * A handle to the current framing object

 4. It then sends a request and waits
 5. The protocol recieves data and processes its frame:

   * If we have a valid frame, we decode it and add the result(7)
   * Otherwise we continue(6)

 6. Afterwards, we instruct the producer to send the next request
 7. Upon adding a result:

   * The factory uses the handler object to translate the TID to a request
   * Using the request paramaters, we corretly store the resulting data
   * Each result is put into the appropriate store

 7. When all the requests have been processed:

   * we stop the producer
   * disconnect the protocol
   * return the factory results

Todo:
 * Build a repeated request producer?
 * Simplify request <-> response linking

