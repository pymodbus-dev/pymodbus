"""
Implementation of a Trio Modbus Server
------------------------------------------

"""
from binascii import b2a_hex
import functools
import logging
import traceback

import trio

from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.factory import ServerDecoder
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.pdu import ModbusExceptions as merror

_logger = logging.getLogger(__name__)


class Executor:
    """
    A helper class to handle the callback interface and feed the result into
    the backend channels.
    """
    def __init__(self, addr, context, response_send, ignore_missing_slaves, broadcast_enable):
        """
        :param addr: An (interface, port) to bind to.
        :param context: The ModbusServerContext datastore
        :param response_send: The response send channel
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
        :return:
        """
        self.addr = addr
        self.context = context
        self.response_send = response_send
        self.ignore_missing_slaves = ignore_missing_slaves
        self.broadcast_enable = broadcast_enable

    def execute(self, request):
        """ The callback to call with the resulting message

        :param request: The decoded request message
        """

        broadcast = False
        try:
            if self.broadcast_enable and request.unit_id == 0:
                broadcast = True
                # if broadcasting then execute on all slave contexts, note response will be ignored
                for unit_id, unit_context in self.context:
                    response = request.execute(unit_context)
            else:
                context = self.context[request.unit_id]
                response = request.execute(context)
        except NoSuchSlaveException as ex:
            _logger.debug("requested slave does not exist: %s" % request.unit_id)
            if self.ignore_missing_slaves:
                return  # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as ex:  # pragma: no cover
            _logger.debug(
                "Datastore unable to fulfill request: %s; %s", ex, traceback.format_exc()
            )
            response = request.doException(merror.SlaveFailure)

        # no response when broadcasting
        if not broadcast:
            response.transaction_id = request.transaction_id
            response.unit_id = request.unit_id
            self.response_send.send_nowait((response, self.addr))


async def incoming(server_stream, framer, context, response_send, ignore_missing_slaves, broadcast_enable):
    """
    Process the incoming data stream and feed it to the framer.
    :return:
    """
    async with response_send:
        units = context.slaves()
        if not isinstance(units, (list, tuple)):  # pragma: no cover
            units = [units]

        async for data in server_stream:
            # TODO: implement UDP support
            # if isinstance(data, tuple):
            #     data, *addr = data  # addr is populated when talking over UDP
            # else:
            #     addr = (None,)  # empty tuple
            addr = (None,)  # empty tuple

            executor = Executor(
                addr=addr,
                context=context,
                response_send=response_send,
                ignore_missing_slaves=ignore_missing_slaves,
                broadcast_enable=broadcast_enable,
            )

            framer.processIncomingPacket(
                data=data,
                callback=executor.execute,
                unit=units,
                single=context.single,
            )


async def tcp_server(server_stream, context, identity, ignore_missing_slaves=False, broadcast_enable=False):
    """
    :param server_stream: The TCP stream.  Generally provided by ``trio.serve_tcp()``.
    :param context: The ModbusServerContext datastore
    :param identity: An optional identity structure
    :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
    :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
    :return:
    """
    if broadcast_enable:
        units = context.slaves()
        if 0 not in context:
            units.append(0)

    response_send, response_receive = trio.open_memory_channel(max_buffer_size=0)
    framer = ModbusSocketFramer(decoder=ServerDecoder(), client=None)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            functools.partial(
                incoming,
                server_stream=server_stream,
                framer=framer,
                context=context,
                response_send=response_send,
                ignore_missing_slaves=ignore_missing_slaves,
                broadcast_enable=broadcast_enable,
            )
        )

        async for message, addr in response_receive:
            if message.should_respond:
                pdu = framer.buildPacket(message)
                if _logger.isEnabledFor(logging.DEBUG):
                    # avoids the b2a_hex() conversion
                    _logger.debug('send: [%s]- %s' % (message, b2a_hex(pdu)))
                if addr == (None,):
                    await server_stream.send_all(pdu)
                else:  # pragma: no cover
                    # TODO: implement UDP support
                    # self._send_(pdu, *addr)
                    pass
            else:   # pragma: no cover
                pass
