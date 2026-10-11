# Security Policy

## Supported Versions

Only the latest version are supported.

## Reporting a Vulnerability

Please be aware that ModbusTcpServer, ModbusUdpServer, ModbusSimulatorServer as well as AsyncModbusTcpClient,
ModbusTcpClient, AsyncModbusUdpClient, ModbusUdpClient are not safe to be used on non-private networks. This is pr
modbus standard. Security reports telling they are not safe, are not accepted because it is a non-valid usage.

For non-private networks please use ModbusTlsServer, AsyncModbusTlsClient or ;odbusTlsClient. Using the correct
certificate is an app issue and considered out of scope for pymodbus. The App can choose to e.g. use a
self-signed certificates which are considered insecure.

Most vulnerabilities like e.g. a buffer overrun should just be reported as a normal issue, since it really is a bug,
allowing all users to be aware of the problem.
