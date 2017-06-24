#!/usr/bin/python
# connect LED to GPIO22 (pin 15)  
import time  
import RPi.GPIO as GPIO  
GPIO.setmode(GPIO.BCM)  
for x in range(0,10):  
  GPIO.setup(22, GPIO.OUT)  
  GPIO.output(22, True)  
  time.sleep(0.05)  
  GPIO.output(22, False)  
  time.sleep(0.45)  
  
GPIO.cleanup()  
