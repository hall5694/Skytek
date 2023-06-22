#!/usr/bin/python3
import sys
import time
import threading
import queue
import multiprocessing
import serial
import time
import atexit

from adafruit_servokit import ServoKit
kit = ServoKit(address=0x44,channels=16)

def turnOffMotors():
    print("Turning off motors")
    kit.servo[3].angle = 35
    time.sleep(2)
    #kit.servo[3].angle = None
    #kit.continuous_servo[2].throttle = 0
    
atexit.register(turnOffMotors)



#kit.servo[0].set_pulse_width_range(500, 2500)
#kit.servo[0].actuation_range = 270
kit.servo[3].set_pulse_width_range(500, 2500)
kit.servo[3].actuation_range = 180

#kit.servo[3].angle = 135
#time.sleep(3)

#kit.servo[3].angle = 90
#time.sleep(2)
#i = 0

'''
for i in range(45,135,10):
    print(i)
    i += 0.1
    kit.servo[3].angle = i
    time.sleep(.7)
'''
time.sleep(2)
#kit.servo[0].angle = None
#time.sleep(1)
#kit.servo[0].angle = 260
#time.sleep(1)
#kit.servo[0].angle = None
#time.sleep(1)
#print(kit.servo[0].angle)



#st = time.time()
#kit.continuous_servo[2].throttle = 0.6
#print(kit.continuous_servo[2].throttle)
#time.sleep(0.1)
#kit.continuous_servo[2].throttle = 0
#print(kit.continuous_servo[2].throttle)
#et = time.time() - st
#print(et)

'''
kit.servo[0].angle = 135
for i in range(20):
    time.sleep(1)
    print(kit.servo[0].angle)
'''



'''
i = 190
kit.servo[0].angle = i
time.sleep(5)
kit.servo[0].angle = 0
'''
'''
while i < 260:
    kit.servo[0].angle = i
    time.sleep(0.25)
    i += 1
    print(i)
    print(kit.servo[0].angle)
'''
'''
while i < 260:
    kit.servo[1].angle = i
    time.sleep(0.25)
    i += 1
    print(i)
    print(kit.servo[1].angle)    
'''