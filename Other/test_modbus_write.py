from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.compat import iteritems
from collections import OrderedDict
from os import system
import time



client = ModbusTcpClient('192.168.88.86', port=502)
client.connect()

builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
builder.add_32bit_float(0)
payload = builder.build()

client.write_registers(8000, payload, skip_encode=True, unit=1)
#client.connect()
#client.write_coil(1, True)
#for i in range(0,100):]
num_reg = 2

'''
for i in range(0,20):
    try:
        result = client.read_holding_registers(8000, num_reg, unit=1) # register start, number of registers, unit id
    except:
        print("problem")   
    else:
        try:     
            decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Little)
        except:
            print("decoder problem")
        else:          
            reg_arr = []
            for i in range(0,int(num_reg / 2)):
                reg_arr.append(decoder.decode_32bit_float())
                if 1:
                    print("{0:0.0f}".format(reg_arr[i]))
                    time.sleep(.05)
decoded = OrderedDict([
('string', decoder.decode_string(8)),
('bits', decoder.decode_bits()),
('8int', decoder.decode_8bit_int()),
('8uint', decoder.decode_8bit_uint()),
('16int', decoder.decode_16bit_int()),
('16uint', decoder.decode_16bit_uint()),
('32int', decoder.decode_32bit_int()),
('32uint', decoder.decode_32bit_uint()),
('32float', decoder.decode_32bit_float()),
('32float2', decoder.decode_32bit_float()),
('64int', decoder.decode_64bit_int()),
('64uint', decoder.decode_64bit_uint()),
('ignore', decoder.skip_bytes(8)),
('64float', decoder.decode_64bit_float()),
('64float2', decoder.decode_64bit_float()),
])



for name, value in iteritems(decoded):
    print("%s\t" % name, hex(value) if isinstance(value, int) else value)
'''
#j = 0
#for i in range(0,2):
#    print("700%s %s" %(j, result.registers[i]))
#    j += 2
    
#newr = result.registers[0].decoder.decode_16bit_int()
#print(newr)
#newresult = result.decode(word_order=little, byte_order=little, formatters=float64)
#print(result)
client.close() 
