#!/usr/bin/python
import time
import datetime
import MySQLdb
import thread
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

temp = 0
i_temp = 0
pressure =0
humidity = 0

try:
    import rrdtool
except:
    print "No python rrdtool package - 'sudo aptitude install python-rrdtool'"
    exit(1)

#-------------------------------------------------------------------------
try:
	rrdtool.create("enviro.rrd", "--step", "15", "--start", "now","--no-overwrite",
	"DS:temp:GAUGE:60:-40.0:50.0",
	"DS:i_temp:GAUGE:60:-40.0:50.0",
	"DS:hum:GAUGE:60:0:100",
	"DS:pres:GAUGE:60:0:U",
	"RRA:AVERAGE:0.5:1:600",
	"RRA:AVERAGE:0.5:30:17520")
except:
        # assume error is because db already exists
        pass

def mysqldata():
	try:
		db = MySQLdb.connect(host="localhost",
			user="root",
			passwd="koen00",
			db="enviro")
	except:
		print "Can't open database enviro on localhost"

	cur=db.cursor()
	while True:
		time.sleep(10*60)
		cmd = "INSERT INTO `data` (`date`,`temp`,`hum`,`pres`) VALUES ('" + \
		datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") +"'," \
		+ format(temp) +"," + format(humidity) +"," + \
		format(pressure) + ")"
		cur.execute(cmd)
		db.commit()

def read_serial():
	global temp,i_temp, pressure, humidity

	while True:
		try:
        		strline=ser.readline()
#		        print(strline)
			x = strline[0]
			if x in "T":
				temp = float(strline[1:])/100.0
				print 'Temp      = {0:0.1f} deg C'.format(temp)
			if x in "t":
				i_temp = float(strline[1:])/100.0
				print 'Indoor Temp  = {0:0.1f} def C'.format(i_temp)
			if x in "H":
				humidity = float(strline[1:])/10.0
				print 'Humidity  = {0:0.1f} %'.format(humidity)
			if x in "P":
				pressure = float(strline[1:])/10.0
				print 'Pressure  = {0:0.1f} hPa'.format(pressure)
		except:
			print("No data received")
		        pass

def rrddata():
	while True:
		global temp,i_temp, pressure, humidity
		time.sleep(30) 
		print datetime.datetime.now()
		#rrdtool format
		udata = "N:"+format(temp)+":"+format(i_temp)+":"+format(humidity)+":"+format(pressure)
		rrdtool.update("enviro.rrd",udata)


try:
	thread.start_new_thread(read_serial,())
	thread.start_new_thread(mysqldata,())
	thread.start_new_thread(rrddata,())
except:
	print "error: unable to start thread"

while 1:
	time.sleep(10)
	pass

db.close