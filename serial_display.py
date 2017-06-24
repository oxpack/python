#!/usr/bin/python
import time
import serial
try:
	ser = serial.Serial('/dev/ttyACM0', 9600)
except:
	print "No /dev/ttyACM0"
	flag = 1
if(flag == 1):
	try:
		ser = serial.Serial('/dev/ttyUSB0', 9600)
	except:
		print "No /dev/ttyUSB0 either. Give up."
		exit (1)
while(1):
	state=ser.readline()
	print(state)
