#!/usr/bin/python3
import time
import board
import busio
import adafruit_ina260
from adafruit_motorkit import MotorKit

kit = MotorKit(address = 0x60)
p_kit = MotorKit(address = 0x61) 

i2c = busio.I2C(board.SCL, board.SDA)
ina260 = adafruit_ina260.INA260(i2c, 0x40)
#ina260_2 = adafruit_ina260.INA260(i2c, 0x41)

sleep_time = 0.2

avg_ma = 0
ma_sum = 0
ma_array=[]


for i in range(0,200):
    current = ina260.current
    ma_array.append(current)
    if len(ma_array) > 10:
        ma_array.pop(0)
    avg_ma = sum(ma_array) / len(ma_array)
    print(ma_array)
    print("Current: %s mA. Avg current: %s" %(current, avg_ma))
    #print("%s Voltage: %s V" %(msg, ina260.voltage))
    #print("%s Power: %s mW" %(msg, ina260.power))
    time.sleep(.1)
        
'''
def print_levels(msg, var):
    ma_sum = 0
    for i in range(0,20):
        current = ina260.current
        ma_sum = ma_sum + current
        avg_ma = ma_sum / (i + 1)
        print("%s Current: %s mA. Avg current: %s" %(msg, current, avg_ma))
        #print("%s Voltage: %s V" %(msg, ina260.voltage))
        #print("%s Power: %s mW" %(msg, ina260.power))
        time.sleep(var / 20)



def print_levels_2(msg, var):
    ma_sum = 0
    for i in range(0,20):
        current = ina260_2.current
        ma_sum = ma_sum + current
        avg_ma = ma_sum / (i + 1)
        print("%s Current: %s mA. Avg current: %s" %(msg, current, avg_ma))
        #print("%s Voltage: %s V" %(msg, ina260_2.voltage))
        #print("%s Power: %s mW" %(msg, ina260_2.power))
        time.sleep(var / 20)        
    


for i in range(0,1):
    #p_kit.motor3.throttle = -1
    #print_levels("outlet open", sleep_time)
    p_kit.motor3.throttle = 1
    print_levels("outlet close", sleep_time)
    p_kit.motor3.throttle = 0
    p_kit.motor3.throttle = None
    time.sleep(0.25)
'''
'''    
for i in range(0,1):
    #p_kit.motor4.throttle = -1
    #print_levels_2("inlet open", sleep_time)
    p_kit.motor4.throttle = 1
    print_levels_2("inlet close", sleep_time)
    p_kit.motor4.throttle = 0
    p_kit.motor4.throttle = None
    time.sleep(0.25)    
#'''


