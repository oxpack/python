#!/usr/bin/python
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)  
GPIO.setup(18, GPIO.OUT)
pwm = GPIO.PWM(18, 100)
pwm.start(0)
while 1:
	for i in range(5,100,2):
		pwm.ChangeDutyCycle(i)
		print(i)
		time.sleep(.051)	
	for i in range(100,5,-2):
		pwm.ChangeDutyCycle(i)
		print(i)
		time.sleep(.05)
