#!/usr/bin/python

import os
import rrdtool

#-------------------------------------------------------------------------
def make_graph(db,duration):
	base_db , ext = os.path.splitext(db)
	text_label = ['Temperature C','%','hectopascals']
	data = ['temp','hum','pres']
	for i in range(0,3):
		filename=base_db+'_'+data[i]+'_'+duration+'.png'
		title = base_db +' '+data[i]+' '+ duration + '\n(UTC)'
		rrdtool.graph(filename,
    	        '--imgformat','PNG',
        	    '--width','750',
            	'--height','250',
	            '--start',duration,
	            #'--left-axis-format','%.1f',
    	        '--vertical-label',text_label[i],
	            '--title',title,
    	        'DEF:val_ave='+ db +':'+ data[i]+':AVERAGE',
	            'LINE1:val_ave#444444',
    	        'GPRINT:val_ave:LAST:Last Reading\: %2.2lf'
				)
	return

make_graph("enviro.rrd","end-1h")
make_graph("enviro.rrd","end-1d")
make_graph("enviro.rrd","end-1w")
make_graph("enviro.rrd","end-1m")
