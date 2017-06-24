#!/usr/bin/python
import rrdtool

rrdtool.graph('dewpoint.png',
   	'--imgformat','PNG', '--width','600',
	'--height','350',
	'--start','end-1d',
   	'--vertical-label','Temperature(C)',
	'DEF:val_ave1=enviro.rrd:temp:AVERAGE',
	'DEF:val_ave2=enviro.rrd:i_temp:AVERAGE',
	'DEF:humidity=enviro.rrd:hum:AVERAGE',
	'CDEF:dewp=val_ave1,100,humidity,-,5,/,-',
	'LINE1:val_ave1#2874A6',
	'LINE2:val_ave2#000000',
	'LINE3:dewp#006000',
	'GPRINT:val_ave1:LAST:Last outside reading\:%2.1lf',
	'GPRINT:val_ave2:LAST:Last inside reading\:%2.1lf'
	)

#Td = T - ((100 - RH)/5.)



