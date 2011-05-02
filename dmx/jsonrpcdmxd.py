#!/usr/bin/env python

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

import sys
import serial
import time
from threading import Thread

ser = serial.Serial('/dev/dmx', 38400, timeout=1)

channels = [8, 16]
devices = []

channelA = 8
channelB = 16

steps = [0.3, -0.5, 0.7]
stepA1 = 0.3
stepA2 = -0.5
stepA3 = 0.7
    
curValA = [ 50, 0, 150 ]
curChangeA =  [ stepA1, stepA2, stepA3 ]
 
stepB1 = -0.2
stepB2 = 0.3
stepB3 = 0.1

curValB = [ 0, 150, 50 ]

curChangeB =  [ stepB1, stepB2, stepB3 ]


step = 1

class DMXDevice(Thread):
    alarmstep = 1
    alarmval = 0
   
    def __init__ (self,channel):
       Thread.__init__(self)
       self.channel = channel
       self.program = 0
       self.sleeptime = 1
       self.step = 1
       self.running = False
       self.alarmstep = 10
       self.alarmval = 0

    def mode_static():
        return 0

    def run(self):
        self.running = True
        while self.running:
            if self.program == 1:
                background(self)
            elif self.program == 2:
                testprogram(self)
            elif self.program == 42:
                self.alarm(self)
            else:
	        time.sleep(self.sleeptime)

    def setprogram(self, program):
        print 'setprogram(%d)' % program
        self.program = program

    def disable(self):
        self.running = False
        return 0

    def alarm(self, device):
        self.alarmval += self.alarmstep
        if self.alarmval >= 300:
            self.alarmstep *= -1
        elif self.alarmval <= 0:
            self.alarmstep *= -1
        rgbc(channelA, self.alarmval, 0, 0)
        rgbc(channelB, self.alarmval, 0, 0)
        time.sleep(0.01)
    

def testprogram(device):
    if device.step == 1:
        device.step = 0
        print "wohoooo"
    rgbc(channelA, 255, 0, 255)
    rgbc(channelB, 0, 255, 0)
    time.sleep(1)
    rgbc(channelA, 0, 255, 0)
    rgbc(channelB, 255, 0, 255)
    time.sleep(1)

def background(device):
    for i in range(0,3):
        curValA[i] += curChangeA[i]

        if (curValA[i] >= 255):
            curValA[i] = 255
            curChangeA[i] = curChangeA[i] * -1
        elif (curValA[i] <= 0):
            curValA[i] = 0
            curChangeA[i] = curChangeA[i] * -1

            if (curChangeA[i] == stepA1):
                curChangeA[i] = stepA2
            elif (curChangeA[i] == stepA2):
                curChangeA[i] = stepA3
            elif (curChangeA[i] == stepA3):
                curChangeA[i] = stepA1

        curValB[i] += curChangeB[i]
    
        if (curValB[i] >= 255):
            curValB[i] = 255
            curChangeB[i] = curChangeB[i] * -1
        elif (curValB[i] <= 0):
            curValB[i] = 0
            curChangeB[i] = curChangeB[i] * -1
    
        if (curChangeB[i] == stepB1):
            curChangeB[i] = stepB2
        elif (curChangeB[i] == stepB2):
            curChangeB[i] = stepB3
        elif (curChangeB[i] == stepB3):
            curChangeB[i] = stepB1

        rgbc(channelA, int(curValA[0]), int(curValA[1]), int(curValA[2]))
        rgbc(channelB, int(curValB[0]), int(curValB[1]), int(curValB[2]))
        
        time.sleep(0.1)

def rgbc(channel, red, green, blue):
    if red > 255: red = 255
    if red < 0: red = 0
    if green > 255: green = 255
    if green < 0: green = 0
    if blue > 255: blue = 255
    if blue < 0: blue = 0
    ser.write("C{0:03d}L000".format(channel-1));
    ser.write("C{0:03d}L{1:03d}".format(channel+0, red));
    ser.write("C{0:03d}L{1:03d}".format(channel+1, green));
    ser.write("C{0:03d}L{1:03d}".format(channel+2, blue));
    ser.write("C{0:03d}L000".format(channel+3));
    return '%d/%d/%d' % (red, green, blue)

def rgb(red, green, blue):
    for channel in channels:
        rgbc(channel, red, green, blue)

def setcolor(color):
    setprogram(0)
    time.sleep(1)
    if color in ['red', 'rot', 'puff', 'sexy']:
        red()
    elif color in ['blue', 'blau']:
        blue()
    elif color in ['black', 'schwarz', '0', 'cdu']:
	rgb(0,0,0)
    elif color in ['white', 'weiss', '1']:
        rgb(255,255,255)
    elif color in ['green', 'gruen']:
        rgb(0,255,0)
    elif color in ['yellow', 'gelb', 'fdp']:
        rgb(255,255,0)
    elif color[0] == '#':
    	n = eval('0x'+color[1:])
    	rgb((n>>16)&0xff, (n>>8)&0xff, n&0xff)
    else: return -1
    return 0
 
def red():
    rgb(255, 0, 0)
    return "red it is"

def green():
    rgb(0, 255, 0)
    return "green it is"

def blue():
    rgb(0, 0, 255)
    return "blue it is"

def white():
    rgb(255, 255, 255)
    return "white it is"

def yellow():
    rgb(255, 255, 0)
    return "yellow it is"

def purple():
    rgb(255, 0, 255)
    return "purple it is"

def enable():
    ser.write("B0")
    return "enabled"

def disable():
    ser.write("B1")
    return "disabled"

def die():
    for device in devices:
        device.disable()
    return "I tried my best"

#for channel in channels:
   #current = DMXDevice(channel)
   #devices.append(current)
   #current.start()

#def run():
#   current = DMXDevice(8)
#   devices.append(current)
#   current.start()

def setprogram(program):
    for device in devices:
        device.setprogram(program)
  
def shutdown():
    setprogram(0)
    
    
step = 0

current = DMXDevice(8)
devices.append(current)
current.start()

server = SimpleJSONRPCServer(('0.0.0.0', 8080))

server.register_function(rgb, 'rgb')
server.register_function(red, 'red')
server.register_function(green, 'green')
server.register_function(blue, 'blue')
server.register_function(white, 'white')
server.register_function(yellow, 'yellow')
server.register_function(purple, 'purple')
server.register_function(enable, 'enable')
server.register_function(enable, 'on')
server.register_function(disable, 'disable')
server.register_function(disable, 'off')
server.register_function(shutdown, 'shutdown')
server.register_function(setcolor, 'setcolor')
#server.register_function(run, 'run')
server.register_function(setprogram, 'setprogram')
server.register_function(die, 'die')
server.serve_forever()
