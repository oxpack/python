#! /usr/bin/env python

# read data from incubator
# record data in RRD (round robin database)
# send email when values are out of bounds

import argparse
import curses
import datetime
import glob
import os
import shutil
import smtplib
import sys
import time

try:
    import serial
except:
    print "No python serial package - 'sudo aptitude install python-serial'"
    exit(1)
try:
    import rrdtool
except:
    print "No python rrdtool package - 'sudo aptitude install python-rrdtool'"
    exit(1)

#-------------------------------------------------------------------------
def make_graph(num,db,duration):
    base_db , ext = os.path.splitext(db)
    filename=str(num)+base_db+'_'+duration+'.png'
    title = str(num) +' '+ base_db +' ' + duration + '\n(UTC)'
    text_label = {'incubator-temp.rrd':'Temperature C','incubator-rh.rrd':'%','incubator-co2.rrd':'pp psi'}
    rrdtool.graph(filename,
            '--imgformat','PNG',
            '--width','750',
            '--height','250',
            '--start',duration,
            #'--left-axis-format','%.1f',
            '--vertical-label',text_label[db],
            '--title',title,
            'DEF:val_ave='+ db +':value:AVERAGE',
            'LINE1:val_ave#444444',
            'GPRINT:val_ave:LAST:Last Reading\: %2.2lf'
            )
    return

#-------------------------------------------------------------------------
def open_serial(device):
    ser = serial.Serial(
            port = device,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout = 15
          )
    return ser

#-------------------------------------------------------------------------
def send_email(subj, msg):
    sender = 'root@incubator.colorado.edu'
    receivers = ['incubator-alarm@bioserve.colorado.edu']

    message = """From: Incubator <root@incubator.colorado.edu>
To: Incubator Alarm <incubator-alarm@bioserve.colorado.edu>
Subject: %s

%s
""" % (subj, msg)

    smtpObj = smtplib.SMTP('localhost')
    smtpObj.sendmail(sender, receivers, message)
    smtpObj.quit()
    return

#-------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('-Tsp',  default=37.0, type=float,
                    help='Temperature Set Point Celsius (default 37.0)')
parser.add_argument('-Csp',  default=0.73, type=float,
                    help='CO2 Set Point partial pressure psi (default 0.73)')
parser.add_argument('-t', default=20.0, type=float,
                    help='Low temperature limit (default 20.0)')
parser.add_argument('-T', default=50.0, type=float,
                    help='High temperature limit (default 50.0)')
parser.add_argument('-Th', default=0.5, type=float,
                    help='Temperature alarm hysteresis (default 0.5)')
parser.add_argument('-r', default=0, type=int,
                    help='Low relative humidity limit (default 0)')
parser.add_argument('-R', default=100, type=int,
                    help='High relative humidity limit (default 100)')
parser.add_argument('-Rh', default=5, type=int,
                    help='Relative humidity hysteresis (default 5)')
parser.add_argument('-c', default=0.00, type=float,
                    help='Low CO2 partial pressure limit (default 0.00)')
parser.add_argument('-C', default="2.00", type=float,
                    help='High CO2 partial pressure limit (default 2.00)')
parser.add_argument('-Ch', default="0.01", type=float,
                    help='CO2 partial pressure hysteresis (default 0.01)')
parser.add_argument('-w', default=1800, type=int,
                    help='Seconds before resending alarm email (default 1800 = 30min)')
parser.add_argument('-s', default="/dev/ttyACM0", type=str,
                    help='Name of serial device (default /dev/ttyACM0)')
a = parser.parse_args()

#-------------------------------------------------------------------------
DBtemp = "incubator-temp.rrd"
DBrh   = "incubator-rh.rrd"
DBco2  = "incubator-co2.rrd"

# Create Round Robin Databases (if they do not already exist)
def createRRD(db, dataname, lo, hi):
    try:
        rrdtool.create(db, '--start', 'now', '--step', '15', '--no-overwrite',
                       'DS:%s:GAUGE:60:%d:%d' % (dataname, lo, hi),
                       'RRA:AVERAGE:0.5:1:1440',
                       'RRA:AVERAGE:0.5:30:17520',
                      )
    except:
        # assume error is because db already exists
        pass
    return

# separate database for each chamber and each data point
createRRD(DBtemp, 'value', 10,  50)
createRRD(DBrh,   'value',  0, 100)
createRRD(DBco2,  'value',  0, 100)

#-------------------------------------------------------------------------
# put a message on screen at specified row, first clearing old text on row
def message(row, msg):
    stdscr.move(row, 0)
    stdscr.clrtoeol()
    stdscr.addstr(msg)
    return

# put a message on screen at specified row, half way across
def message2(row, msg):
    stdscr.move(row, 40)
    stdscr.addstr(msg)
    return

# put a multi-line message on screen starting at specified row, first
# clearing old text from here to bottom of screen
def err_message(msg):
    stdscr.move(R_ERR, 0)
    stdscr.clrtobot()
    stdscr.addstr(msg)
    return

#-------------------------------------------------------------------------
inAlarm = False
sendAlarms = True
firstTime = True
alarmTime = 0
count = 0
ser = open_serial(a.s)

# define screen rows for messages
R_banner = 0
R_ts = 2
R_t = 3
R_rh = 4
R_co2 = 5
R_alarm = 6
R_sendalarm = 7
R_DEBUG = 9
R_ERR = 10

# everything below is in a try/finally block so we can restore the screen
# before quitting
stdscr = curses.initscr()
try:
    curses.noecho() # do not echo keystrokes
    curses.cbreak() # get individual keystrokes, don't wait for a whole line
    stdscr.nodelay(True) # if there is no keystroke, don't wait, return -1
    stdscr.keypad(True) # process arrow keys and such as a single keystroke
    stdscr.clear() # clear screen
    stdscr.refresh() # draw screen

    # need delay after arduino is reset
    message(R_DEBUG, "Waiting for Arduino to reset...")
    stdscr.refresh()
    time.sleep(5)

    # send setpoints
    com_str = "T"+str(a.Tsp)+"\r"
    message(R_DEBUG, com_str)
    stdscr.refresh()
    ser.write(com_str.encode())
    time.sleep(1)

    com_str = "C"+str(a.Csp)+"\r"
    message(R_DEBUG, com_str)
    stdscr.refresh()
    ser.write(com_str.encode())
    time.sleep(1)

    # when we start the program, set the alarm state. that way, we
    # will skip the initial settling-in period and not send spurious
    # emails. after the standard wait time, or when we first reach a
    # state where all three variables are within the specified range,
    # we'll begin checking for real alarms.
    stdscr.clear()
    inAlarm = True
    alarmTime = time.time()
    ts = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    msg = ts + "\nALARMS IGNORED during startup period\n"
    err_message(msg)

    while True:
        stdscr.refresh()
        message(R_DEBUG, "")
        vals = ser.readline()
        ts = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        message(R_ts, ts)
        if inAlarm:
            message(R_alarm, "Alarm is currently SET")
        else:
            message(R_alarm, "Alarm is currently CLEAR")
        message2(R_alarm, "Seconds between alert emails: %d" % a.w)

        # check for a keypress; -1 if no key pressed
        # note that CTRL-C will still quit the program
        keypress = stdscr.getch()
	if keypress == ord('U'):
	    # start calibration sequence
	    ser.write(chr(keypress))
        if keypress != -1:
            # toggle whether we send alarm emails
            sendAlarms = not sendAlarms
        if sendAlarms:
            message(R_sendalarm, "Alert emails will be sent")
        else:
            message(R_sendalarm, "Alert emails will NOT be sent")
        message2(R_sendalarm, "(press a key to toggle)")

        # check to see if data is a comment ##
        if vals[0:2] =="##":
            message(R_DEBUG, vals)
            continue

        vals = vals.split()
        if not vals:
            message(R_DEBUG, "No vals found on serial input")
            continue
        if len(vals) != 4:
            message(R_DEBUG, "Invalid input, expected 4 values, got: " + repr(vals))
            continue
        channel = vals[0]
        if channel != "0" and channel != "1":
            message(R_DEBUG, "Invalid input, channel not '0' or '1', got: " + repr(vals))
            continue
        try:
            temp = float(vals[1])/10.0
            rh = int(vals[2])
            co2 = float(vals[3])/100.0
        except:
            message(R_DEBUG, "Invalid input, error converting to number, got: " + repr(vals))
            continue

        # display the values we just got
        message(R_banner, "Incubator control system #" + channel)
        message(R_t,    "Temp: %.2f" % (temp))
        message2(R_t,   "[%.2f .. %.2f] setpoint %.2f" % (a.t, a.T, a.Tsp))
        message(R_rh,   "RH:   %d" % (rh))
        message2(R_rh,  "[%d .. %d]" % (a.r, a.R))
        message(R_co2,  "CO2:  %.2f" % (co2))
        message2(R_co2, "[%.2f .. %.2f] setpoint %.2f" % (a.c, a.C, a.Csp))

        # feed updates to the RRD
        rrdtool.update(DBtemp, 'N:%.2f' % temp)
        rrdtool.update(DBrh,   'N:%d' % rh)
        rrdtool.update(DBco2,  'N:%.2f' % co2)

        # make graphs
        count = count + 1
        # every 60 seconds (actually, every 60 data lines read)
        if count%60 == 0:
            for data in ['incubator-temp.rrd','incubator-rh.rrd','incubator-co2.rrd']:
                for i in ['end-1h','end-1d']:
                    make_graph(channel,data,i)
                for file in glob.glob(r'*end-1h*.png'):
                    shutil.copy(file,"/var/www/html")
                for file in glob.glob(r'*end-1d*.png'):
                    shutil.copy(file,"/var/www/html")

        # every 10 minutes (actually, every 600 data lines read)
        if count%605 == 0:
            for data in ['incubator-temp.rrd','incubator-rh.rrd','incubator-co2.rrd']:
                for i in ['end-1w','end-1m']:
                    make_graph(channel,data,i)
                for file in glob.glob(r'*end-1w*.png'):
                    shutil.copy(file,"/var/www/html")
                for file in glob.glob(r'*end-1m*.png'):
                    shutil.copy(file,"/var/www/html")
                # reset the counter
                count = 1

        if inAlarm:
            if (a.t + a.Th) <= temp <= (a.T - a.Th) and \
               (a.r + a.Rh) <= rh <= (a.R - a.Rh) and \
               (a.c + a.Ch) <= co2 <= (a.C - a.Ch):
                # alarm is now clear
                inAlarm = False
                alarmTime = 0
                msg = ts + "\nALARM CLEAR\n"
                msg += ("Incubator %s has nominal temperature %.2f\n" % (channel, temp))
                msg += ("Incubator %s has nominal relative humidity %.2f\n" % (channel, rh))
                msg += ("Incubator %s has nominal carbon dioxide %.2f\n" % (channel, co2))
                if sendAlarms:
                    if not firstTime:
                        send_email("Alarm Clear", msg)
                err_message(msg)
                firstTime = False
                continue

            # still in an alarm state...
            if time.time() - alarmTime < a.w:
                # we have not waited long enough to send another email
                continue

        # we are not in an alarm state, or still are and time to resend email.
        # check for values that are outside limits and send email if bad.
        subj = "ALARM:"
        msg = ts + "\nReason for alarm\n"
        if not((a.t - a.Th) <= temp <= (a.T + a.Th)):
            inAlarm = True
            alarmTime = time.time()
            subj += " Temp"
            msg += ("Incubator %s has temperature %.2f, outside range [%.2f,%.2f]\n" %
                        (channel, temp, a.t, a.T))
        else:
            msg += ("Incubator %s has nominal temperature %.2f\n" % (channel, temp))

        if not((a.r - a.Rh) <= rh <= (a.R + a.Rh)):
            inAlarm = True
            alarmTime = time.time()
            subj += " RH"
            msg += ("Incubator %s has relative humidity %d, outside range [%d,%d]\n" %
                        (channel, rh, a.r, a.R))
        else:
            msg += ("Incubator %s has nominal relative humidity %.2f\n" % (channel, rh))

        if not((a.c - a.Ch) <= co2 <= (a.C + a.Ch)):
            inAlarm = True
            alarmTime = time.time()
            subj += " CO2"
            msg += ("Incubator %s has carbon dioxide %.2f, outside range [%.2f,%.2f]\n" %
                        (channel, co2, a.c, a.C))
        else:
            msg += ("Incubator %s has nominal carbon dioxide %.2f\n" % (channel, co2))

        if inAlarm:
            # we just (re)entered an alarm state, send email
            if sendAlarms:
                send_email(subj, msg)
            err_message(msg)
            # if this is the first time here, then we have waited the
            # full timeout - clear the flag.
            firstTime = False

        # end of loop, return to top and start over. no need to delay,
        # we will wait until there is another line to read.

finally:
    stdscr.keypad(0)
    curses.nocbreak()
    curses.echo()
    curses.endwin()

