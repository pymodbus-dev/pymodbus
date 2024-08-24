Pymodbus simulator ReST API
===========================

This is still a Work In Progress. There may be large changes to the API in the
future.

The API is a simple copy of
having most of the same features as in the Web UI.

The API provides the following endpoints:

- /restapi/registers
- /restapi/calls
- /restapi/server
- /restapi/log

Registers Endpoint
------------------

/restapi/registers
^^^^^^^^^^^^^^^^^^

    The registers endpoint is used to read and write registers.

    **Request Parameters**

    - `submit` (string, required):
        The action to perform. Must be one of `Register`, `Set`.
    - `range_start` (integer, optional):
        The starting register to read from. Defaults to 0.
    - `range_end` (integer, optional):
        The ending register to read from. Defaults to `range_start`.

    **Response Parameters**

    Returns a json object with the following keys:

    - `result` (string):
        The result of the action. Either `ok` or `error`.
    - `error` (string, conditional):
        The error message if the result is `error`.
    - `register_rows` (list):
        A list of objects containing the data of the registers.
    - `footer` (string):
        A cleartext status of the action. HTML leftover.
    - `register_types` (list):
        A static list of register types. HTML leftover.
    - `register_actions` (list):
        A static list of register actions. HTML leftover.

    **Example Request and Response**

    Request Example:

    .. include:: registers_request.rst

    Response Example:

    .. include:: registers_response.rst

Calls Endpoint
--------------

The calls endpoint is used to handle ModBus response manipulation.

/restapi/calls
^^^^^^^^^^^^^^

    The calls endpoint is used to simulate different conditions for ModBus
    responses.

    **Request Parameters**

    - `submit` (string, required):
        The action to perform. Must be one of `Simulate`, `Reset`.

    The following must be present if `submit` is `Simulate`:

    - `response_clear_after` (integer, required):
        The number of packet to clear simulation after.
    - `response_cr` (string, required):
        Must be present but can be any value. Turns on change rate simulation (WIP).
    - `response_cr_pct` (integer, required):
        The percentage of change rate, how many percent of packets should be
        changed.
    - `response_split` (string, required):
        Must be present but can be any value. Turns on split response simulation (WIP).
    - `split_delay` (integer, required):
        The delay in seconds to wait before sending the second part of the split response.
    - `response_delay` (integer, required):
        The delay in seconds to wait before sending the response.
    - `response_error` (integer, required):
        The error code to send in the response. The valid values can be one from
        the response `function_error` list.

    When `submit` is `Reset`, no other parameters are required. It resets all
    simulation options to their defaults (off).

    **Example Request and Response**

    Request:

    .. include:: calls_request.rst

    Response:

    Unfortunately, the endpoint response contains extra clutter due to
    not being finalized.

    .. include:: calls_response.rst

Server Endpoint
---------------

The server endpoint has not yet been implemented.

Log Endpoint
------------

The log endpoint has not yet been implemented.