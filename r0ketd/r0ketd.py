#!/usr/bin/env python

import serial, time, socket, os, sys, re
import jsonrpclib
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

logindelta = 10
timeoutdelta = 240

r0ketmap = {'95471AAF': 'baccenfutter', '244A0407': 'keyboardsurfer', '1854AD15': 'smile', '6DA003CC': 'dazz'}

jsonrpclib.config.version = 1.0
cbeam = jsonrpclib.Server('http://10.0.1.27:4254')

sensor="c_leuse"

def init():
    global ser
    ser = serial.Serial('/dev/ttyACM0',115200,timeout=1)
    ser.setDTR(0)

    ser.open()
    #time.sleep(1)
    #ser.write("2")
    #time.sleep(5)
    #ser.write("2")
    #str = ser.readline()
    return 0

def main():
    init()
    while 1:
        #str = ser.readline()
        line = ser.readline().rstrip('\n')
        if line != "":
            print line
        # RECV 95471AAF: B2007A (100.00)
        result = re.search('RECV (.*): (.*) \((.*)\)', line) 
        if result != None:
            if result.group(1) in r0ketmap.keys():
                print 'r0ket %s detected, logging in %s' % (result.group(1), r0ketmap[result.group(1)])
                cbeam.r0ketseen(result.group(1), sensor, result.group(2), result.group(3))
                result = cbeam.login(r0ketmap[result.group(1)])
            else:
                print 'saw unknown r0ket: %s' % result.group(1)
        sys.stdout.flush()


def toggleWallhack():
    #ser.write("0")
    print "toggleWallhack"
    return "aye"



#while 1:
    #str = ser.read()
    #if len(str) == 1:
        #rec = ord(str)
        #if rec < 128:
            #print rec
            #os.system('%s/%d.sh' % (basedir, rec))

if __name__ == "__main__":
    main()
