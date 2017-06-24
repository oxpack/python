#!/usr/bin/python

import time
from subprocess import call

try:
	import RPi.GPIO as GPIO
except RuntimeError:
	print("Error importing RPi.GPIO")

print GPIO.VERSION

print GPIO.getmode()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(5,GPIO.OUT)
GPIO.setup(16,GPIO.IN,pull_up_down=GPIO.PUD_UP)

i=0

while True:
	i=i+1
	print i
	GPIO.output(5,i%2)
	if(GPIO.input(16) == 0):
		call(["/opt/vc/bin/tvservice","-p"])
		i = 0
	if(i==50):
		call(["/opt/vc/bin/tvservice","-o"])
	time.sleep(.5)

	
