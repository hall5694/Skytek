#!/usr/bin/python3
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import atexit
import time
#kit = MotorKit(address = 0x61)
p_kit = MotorKit(address = 0x62)

def turnOffMotors():
    print("Turning off motors")
    p_kit.stepper2.release()

atexit.register(turnOffMotors)
    
for j in range(10):
    for i in range(200):

        p_kit.stepper2.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
        time.sleep(0.5)
        
        
p_kit.stepper2.release()
    
    
