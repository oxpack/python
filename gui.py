#!/usr/bin/python
from Tkinter import *
import rrdtool
import time
import thread
import tkFont
import RPi.GPIO as GPIO
from PIL import Image,ImageTk
from subprocess import call

def display_pwr(status):
	#status =0 for off
	#status = 100 for on
	#status = 50 for dim
	pwm.ChangeDutyCycle(status)

#-------------------------------------------------------------------------
def make_graph_temp(duration):
	print "make_graph: temp-" + duration
	text_label = 'Temperature (C)'	
	rrdtool.graph('baseimage.png',
    	'--imgformat','PNG', '--width','600',
	'--height','350',
	'--start',duration,
   	'--vertical-label',text_label,
	'DEF:val_ave1='+ rrd_file +':temp:AVERAGE',
	'DEF:val_ave2='+ rrd_file +':i_temp:AVERAGE',
	'DEF:humidity=enviro.rrd:hum:AVERAGE',
	'CDEF:dewp=val_ave1,100,humidity,-,5,/,-',
	'LINE1:val_ave1#2874A6',
	'LINE2:val_ave2#000000',
	'LINE3:dewp#006000',
	'GPRINT:val_ave1:LAST:Last outside reading\:%2.1lf',
	'GPRINT:val_ave2:LAST:Last inside reading\:%2.1lf',
	'GPRINT:dewp:LAST:Last outside dewpoint reading\:%2.1lf'
		)
	return

def make_graph_hum(duration):
	print "make_graph: hum-" + duration
	text_label = 'Humidity (%)'	
	rrdtool.graph('baseimage.png',
    	'--imgformat','PNG', '--width','600',
	'--height','350',
	'--start',duration,
   	'--vertical-label',text_label,
	'DEF:val_ave='+ rrd_file +':hum:AVERAGE',
	'LINE1:val_ave#444444',
	'GPRINT:val_ave:LAST:Last reading\:%2.2lf'
		)
	return

def make_graph_pres(duration):
	print "make_graph: pres-" + duration
	text_label = 'Pressure (hectopascals)'	
	rrdtool.graph('baseimage.png',
    	'--imgformat','PNG', '--width','600',
	'--height','350',
	'--start',duration,
   	'--vertical-label',text_label,
	'DEF:val_ave='+ rrd_file +':pres:AVERAGE',
	'LINE1:val_ave#444444',
	'GPRINT:val_ave:LAST:Last Reading\:%2.2lf'
		)
	return

def make_graph(type,duration):
	if type == 'temp':
		make_graph_temp(duration)
	if type == 'hum':
		make_graph_hum(duration)
	if type == 'pres':
		make_graph_pres(duration)
	return



#array to convert button input to duration
duration_array = [['Hourly','end-1h'],['Daily','end-1d'],['Weekly','end-1w'],['Monthly','end-1m']]

#set up GPIO to do screen dimming
try:
	import RPi.GPIO as GPIO
except RuntimeError:
	print("Error importing RPi.GPIO")

print GPIO.VERSION
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  
GPIO.setup(18, GPIO.OUT)
pwm = GPIO.PWM(18, 100)
pwm.start(100)


#start Tk definitions
win = Tk()
win.configure(background='black',cursor='none')
win.title("Weather")
w,h = win.winfo_screenwidth(), win.winfo_screenheight()
print w,h
win.geometry("%dx%d+0+0" % (w,h))
win.attributes('-fullscreen', True)

#where the rrd_file is located
rrd_file = "/home/pi/python/enviro.rrd"
#make default temperature daily image
dur_i = 0
type = "temp"
duration = "end-1d"
make_graph(type,duration)

myFont = tkFont.Font(family = 'Helvetica', size = 12)

dur_i = 1
type = "temp"
duration = "end-1d"
new_time = int(time.time())

def duration_cycle():
	global dur_i, duration,display
	dur_i = dur_i +1
	print("Cycle duration: " + duration_array[dur_i%4][0])
	durationButton["text"] = duration_array[dur_i%4][0]
	duration = duration_array[dur_i%4][1]	
	make_graph(type,duration)
	display = ImageTk.PhotoImage(Image.open('baseimage.png'))
	label1.configure(image=display)

def radio():
	global type,duration,display
	print(v.get())
	type = v.get()
	make_graph(type,duration)
	display = ImageTk.PhotoImage(Image.open('baseimage.png'))
	label1.configure(image=display)

MODES = [["Temperature","temp"],
	["Humidity","hum"],
	["Pressure","pres"]]

v = StringVar()
v.set("Temp")

for i in range(0,3):
	b= Radiobutton(win,text=MODES[i][0],variable=v,font = myFont, 
		command=radio,
                indicatoron=0,
                value=MODES[i][1],height=2,width=10)
	b.grid(row=i,column=0)

durationButton  = Button(win, text = "Daily", font = myFont, 
	command = duration_cycle, 
	height =1 , width = 6) 
durationButton.grid(row=3,column=1)

display = ImageTk.PhotoImage(Image.open('baseimage.png'))
label1 = Label(win,image=display)
label1.grid(row=0,rowspan=3,column=1,columnspan=2)

strdate = time.strftime('%a, %d %b %Y %X') 
label2 = Label(win,text=strdate, fg="white", bg="black", font=('Helvetica',16))
label2.grid(row=3,column=2)

def task():
	strdate = time.strftime('%a, %d %b %Y %X') 
	label2.configure(text=strdate)
	win.after(500, task)


def sleep():
	global new_time
	while 1:
		age = int(time.time()) - new_time
		if(age == 90):
			display_pwr(10)
		elif age > 100:
			display_pwr(0)
#		print(new_time,int(time.time()))
		time.sleep(1)		

win.after(500, task)

def callback(event):
	global new_time, label1
	if(int(time.time()) > new_time+100):
		make_graph(type,duration)
		img2 = ImageTk.PhotoImage(Image.open('baseimage.png'))
		label1.configure(image=img2)
		label1.image=img2	
		print("Mouse click from wake")
	#reset the clock
	new_time = int(time.time())
	display_pwr(100)
	print("Mouse click")
		
win.bind("<Button-1>", callback)

try:
   thread.start_new_thread( sleep,())
except:
   print "Error: unable to start thread"

mainloop()
