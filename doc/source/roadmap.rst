Roadmap
=======

The roadmap is not a finite plan, but merely an expression of intentions !

Pymodbus development is mainly driven by contributors, who have an itch, and provide a solution for the community.
The maintainers are very open to these pull request, and ONLY work to secure that:

- it does not break existing usage/functionality (PR put on hold for next API change release)
- it is a generic feature (e.g. not just for serial 9.600 bps)
- it have proper test cases, to ensure against side effects.
- it follow the modbus standard

The following bullet points are what the maintainers focus on:

- 3.9.1, with:
    - Currently not planned
- 4.0.0, with:
    - ModbusControlBlock pr slave
    - New custom PDU (function codes)
    - Simulator datastore, with simple configuration
    - Remove remote_datastore
    - Remove BinaryPayload
    - Server becomes Simulator
    - New serial forwarder
    - client async with sync/async API
    - Only one datastore, but with different API`s
    - GUI client, to analyze devices
    - GUI server, to simulate devices

All contributions are WELCOME, and we (the maintainers) are always open to talk about ideas,
best way is via `discussions <https://github.com/pymodbus-dev/pymodbus/discussions>`_ on github.

We have lately decided, that we do strictly follow the `modbus org <https://modbus.org>`_ standard,
but we also accept vendor specific (like Huawei) pull requests, as long as they extend the standard or are actitvated with
a specific argument like --huawei. Note code must be clearly separated
from the main code and marked with a responsible maintainer.
