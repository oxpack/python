#!/usr/bin/python

import MySQLdb
from datetime import datetime

db = MySQLdb.connect(host="localhost",
			user="root",
			passwd="koen00",
			db="enviro")
cur=db.cursor()

cmd = "INSERT INTO `data` (`date`,`temp`,`hum`,`pres`) VALUES ('" + \
	datetime.now().strftime("%Y-%m-%d %H:%M:%S") +"',22.6,26,500)"

print cmd

cur.execute(cmd)
db.commit()
print

cmd = "SELECT * FROM data"
cur.execute(cmd)
for row in cur.fetchall():
	print row



db.close