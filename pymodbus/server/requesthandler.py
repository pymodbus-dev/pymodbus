"""Implementation of a Threaded Modbus Server."""
from __future__ import annotations

import asyncio
import traceback

from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.logging import Log
from pymodbus.pdu.pdu import ExceptionResponse
from pymodbus.transaction import TransactionManager
from pymodbus.transport import CommParams, ModbusProtocol


class ServerRequestHandler(TransactionManager):
    """Handle client connection."""

    def __init__(self, owner):
        """Initialize."""
        params = CommParams(
            comm_name="server",
            comm_type=owner.comm_params.comm_type,
            reconnect_delay=0.0,
            reconnect_delay_max=0.0,
            timeout_connect=0.0,
            host=owner.comm_params.source_address[0],
            port=owner.comm_params.source_address[1],
            handle_local_echo=owner.comm_params.handle_local_echo,
        )
        self.server = owner
        self.framer = self.server.framer(self.server.decoder)
        self.running = False
        self.handler_task = None  # coroutine to be run on asyncio loop
        self.databuffer = b''
        self.loop = asyncio.get_running_loop()
        super().__init__(
            params,
            self.framer,
            0,
            True,
            None,
            None,
            None,
        )

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        Log.debug("callback_new_connection called")
        return ServerRequestHandler(self)

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        super().callback_connected()
        slaves = self.server.context.slaves()
        if self.server.broadcast_enable:
            if 0 not in slaves:
                slaves.append(0)
        try:
            self.running = True

            # schedule the connection handler on the event loop
            self.handler_task = asyncio.create_task(self.handle())
            self.handler_task.set_name("server connection handler")
        except Exception as exc:  # pylint: disable=broad-except
            Log.error(
                "Server callback_connected exception: {}; {}",
                exc,
                traceback.format_exc(),
            )

    def callback_disconnected(self, call_exc: Exception | None) -> None:
        """Call when connection is lost."""
        super().callback_disconnected(call_exc)
        try:
            if self.handler_task:
                self.handler_task.cancel()
            if hasattr(self.server, "on_connection_lost"):
                self.server.on_connection_lost()
            if call_exc is None:
                Log.debug(
                    "Handler for stream [{}] has been canceled", self.comm_params.comm_name
                )
            else:
                Log.debug(
                    "Client Disconnection {} due to {}",
                    self.comm_params.comm_name,
                    call_exc,
                )
            self.running = False
        except Exception as exc:  # pylint: disable=broad-except
            Log.error(
                "Datastore unable to fulfill request: {}; {}",
                exc,
                traceback.format_exc(),
            )

    async def handle(self) -> None:
        """Coroutine which represents a single master <=> slave conversation.

        Once the client connection is established, the data chunks will be
        fed to this coroutine via the asyncio.Queue object which is fed by
        the ServerRequestHandler class's callback Future.

        This callback future gets data from either asyncio.BaseProtocol.data_received
        or asyncio.DatagramProtocol.datagram_received.

        This function will execute without blocking in the while-loop and
        yield to the asyncio event loop when the frame is exhausted.
        As a result, multiple clients can be interleaved without any
        interference between them.
        """
        while self.running:
            try:
                pdu, *addr, exc = await self.server_execute()
                if exc:
                    pdu = ExceptionResponse(
                        40,
                        exception_code=ExceptionResponse.ILLEGAL_FUNCTION
                    )
                    self.server_send(pdu, 0)
                    continue
                await self.server_async_execute(pdu, *addr)
            except asyncio.CancelledError:
                # catch and ignore cancellation errors
                if self.running:
                    Log.debug(
                        "Handler for stream [{}] has been canceled", self.comm_params.comm_name
                    )
                    self.running = False
            except Exception as exc:  # pylint: disable=broad-except
                # force TCP socket termination as framer
                # should handle application layer errors
                Log.error(
                    'Unknown exception "{}" on stream {} forcing disconnect',
                    exc,
                    self.comm_params.comm_name,
                )
                self.close()
                self.callback_disconnected(exc)

    async def server_async_execute(self, request, *addr):
        """Handle request."""
        broadcast = False
        try:
            if self.server.broadcast_enable and not request.dev_id:
                broadcast = True
                # if broadcasting then execute on all slave contexts,
                # note response will be ignored
                for dev_id in self.server.context.slaves():
                    response = await request.update_datastore(self.server.context[dev_id])
            else:
                context = self.server.context[request.dev_id]
                response = await request.update_datastore(context)

        except NoSuchSlaveException:
            Log.error("requested slave does not exist: {}", request.dev_id)
            if self.server.ignore_missing_slaves:
                return  # the client will simply timeout waiting for a response
            response = ExceptionResponse(0x00, ExceptionResponse.GATEWAY_NO_RESPONSE)
        except Exception as exc:  # pylint: disable=broad-except
            Log.error(
                "Datastore unable to fulfill request: {}; {}",
                exc,
                traceback.format_exc(),
            )
            response = ExceptionResponse(0x00, ExceptionResponse.SLAVE_FAILURE)
        # no response when broadcasting
        if not broadcast:
            response.transaction_id = request.transaction_id
            response.dev_id = request.dev_id
            self.server_send(response, *addr)

    def server_send(self, pdu, addr):
        """Send message."""
        if not pdu:
            Log.debug("Skipping sending response!!")
        else:
            self.pdu_send(pdu, addr=addr)
