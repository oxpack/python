#!/usr/bin/python

import os
import rrdtool

#-------------------------------------------------------------------------
def make_graph(db,duration):
	i=0
	base_db , ext = os.path.splitext(db)
	text_label = ['Temperature C','%','hectopascals']
	data = ['temp','hum','pres']
	filename='2-3week.png'
	title = '2-3week'
	rrdtool.graph(filename,
        '--imgformat','PNG',
       	'--width','750',
       	'--height','250',
        '--start','end-3w',
	'--end','-2w',
        '--vertical-label',text_label[i],
       	'--title',title,
        'DEF:val_ave='+ db +':'+ data[i]+':AVERAGE',
	'LINE1:val_ave#444444',
        'GPRINT:val_ave:LAST:Last Reading\: %2.2lf'
	)
	return

make_graph("enviro.rrd","end-1h")