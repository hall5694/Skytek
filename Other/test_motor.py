#!/usr/bin/python3
import sys
import time
import threading
import queue
import multiprocessing
import serial
import time
import atexit

from adafruit_motorkit import MotorKit
kit = MotorKit(address = 0x60)
p_kit = MotorKit(address = 0x61)

'''
def stop_all_motors():
    p_kit.motor1.throttle = 0
    p_kit.motor1.throttle = None
    

for i in range(0,1):
    p_kit.motor1.throttle = -1
    time.sleep(1)
    print(p_kit.motor1.throttle)
    p_kit.motor1.throttle = 1
    time.sleep(1)    
    print(p_kit.motor4.throttle)
    p_kit.motor4.throttle = 0
    print(p_kit.motor4.throttle)
    p_kit.motor4.throttle = None
    print(p_kit.motor4.throttle)
    time.sleep(0.25)
'''

def stop_all_motors():
    kit.motor2.throttle = 0
    kit.motor2.throttle = None
    kit.motor3.throttle = 0
    kit.motor3.throttle = None
    kit.motor4.throttle = 0
    kit.motor4.throttle = None
    p_kit.motor1.throttle = 0
    p_kit.motor1.throttle = None
    p_kit.motor2.throttle = 0
    p_kit.motor2.throttle = None                
    
    
    kit.motor2.throttle = 0.8
    time.sleep(0.05)
    kit.motor2.throttle = 0
    time.sleep(3)
    
    '''
    kit.motor3.throttle = 0.8
    time.sleep(2)
    kit.motor3.throttle = 0
    time.sleep(3)
    
    
    
    kit.motor4.throttle = 0.8
    time.sleep(2)
    kit.motor4.throttle = 0
    time.sleep(3)
    '''
    
    '''
    p_kit.motor1.throttle = 1.0
    time.sleep(3)
    p_kit.motor1.throttle = 0
    time.sleep(3)
    '''
    
    '''
    p_kit.motor2.throttle = 0.8
    time.sleep(3)
    p_kit.motor2.throttle = 0
    time.sleep(3)
    '''       

atexit.register(stop_all_motors)
