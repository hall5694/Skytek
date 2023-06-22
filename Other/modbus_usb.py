#!/usr/bin/env python
import minimalmodbus
import time

# port name, slave address (in decimal)
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1, "rtu", False, True)

instrument.serial.baudrate = 9600
instrument.serial.stopbits = 2

while True:
    # Register number, number of decimals, function code
    temperature = instrument.read_register(5)
    print(temperature)
    time.sleep(1)
