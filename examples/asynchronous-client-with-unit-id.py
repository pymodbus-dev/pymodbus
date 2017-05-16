import pymodbus.client.sync import ModbusTcpClient
client = ModbusTcpClient('192.168.0.107')
res = client.read_holding_registers(3999, 24, unit=2)
print res.registers
