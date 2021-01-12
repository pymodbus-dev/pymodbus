from binascii import b2a_hex
import functools
import logging

import trio

from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.factory import ServerDecoder

_logger = logging.getLogger(__name__)


def execute(request, addr, context, response_send):
    broadcast = False
    try:
        if False:  # self.server.broadcast_enable and request.unit_id == 0:
            broadcast = True
            # if broadcasting then execute on all slave contexts, note response will be ignored
            for unit_id in self.server.context.slaves():
                response = request.execute(self.server.context[unit_id])
        else:
            context = context[request.unit_id]
            response = request.execute(context)
    except NoSuchSlaveException as ex:
        _logger.debug("requested slave does " "not exist: %s" % request.unit_id)
        if False:  # self.server.ignore_missing_slaves:
            return  # the client will simply timeout waiting for a response
        response = request.doException(merror.GatewayNoResponse)
    except Exception as ex:
        _logger.debug(
            "Datastore unable to fulfill request: " "%s; %s", ex, traceback.format_exc()
        )
        response = request.doException(merror.SlaveFailure)
    # no response when broadcasting
    if not broadcast:
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        response_send.send_nowait((response, addr))


class EventAndValue:
    def __init__(self):
        self.event = trio.Event()
        self.value = self


async def incoming(server_stream, framer, context, response_send):
    async with response_send:
        units = context.slaves()
        if not isinstance(units, (list, tuple)):
            units = [units]

        async for data in server_stream:
            if isinstance(data, tuple):
                data, *addr = data  # addr is populated when talking over UDP
            else:
                addr = (None,)  # empty tuple

            framer.processIncomingPacket(
                data=data,
                callback=functools.partial(
                    execute,
                    addr=addr,
                    context=context,
                    response_send=response_send,
                ),
                unit=units,
                single=context.single,
            )


async def tcp_server(server_stream, context, identity):

    # if server.broadcast_enable:  # pragma: no cover
    #     if 0 not in units:
    #         units.append(0)
    if not context.single:
        raise Exception("non-single context not yet supported")
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
            )
        )

        async for message, addr in response_receive:
            if message.should_respond:
                # self.server.control.Counter.BusMessage += 1
                pdu = framer.buildPacket(message)
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("send: [%s]- %s" % (message, b2a_hex(pdu)))
                if addr == (None,):
                    await server_stream.send_all(pdu)
                else:
                    1 / 0
                    self._send_(pdu, *addr)
