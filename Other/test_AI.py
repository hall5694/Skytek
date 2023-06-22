#!/usr/bin/python3
import time
import board
import busio
import adafruit_ina260
from adafruit_motorkit import MotorKit

i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
ads = ADS.ADS1115(i2c, address=0x48)
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)

sleep_time = 0.2
#print(ads.gain)

for i in range(0,1000):
    print("chan0: (%s)  chan1 (%s)  chan2 (%s)"%(format(chan0.voltage,'.4f'),format(chan1.voltage,'.4f'),format(chan2.voltage,'.4f')))
    time.sleep(sleep_time)
