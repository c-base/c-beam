#!/usr/bin/python2.6

import socket

class ArtNet(object):
    def __init__(self, broadcast):
        self.__udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__broadcast = socket.gethostbyname(broadcast)

    def __send(self, packet):
        if packet:
            #print 'sending ', self.__broadcast
            self.__udp.sendto(packet, 0, (self.__broadcast, 6454))
    
    def buildDMXHeader(self):
        # a dmx packet contains every time 512 bytes dmx data
        header = bytearray()
        # id
        header.extend(bytearray('Art-Net'))
        header.append(0x0)
        # opcode low byte first
        header.append(0x00)
        header.append(0x50)
        # proto ver high byte first
        header.append(0x0)
        header.append(14)
        # sequence 
        header.append(0x0)
        # physical port
        header.append(0x0)
        # universe low byte first
        header.append(0x0)
        header.append(0x0)
        # length high byte first
        header.append((512 >> 8) & 0xFF)
        header.append(512 & 0xFF)
        return header

    def sendToDmx(self, dmx):
        if (len(dmx) > 512):
            raise RunTimeError("dmx packet > 512")
        plainDmx = bytearray(512)
        for i in range(len(dmx)):
            plainDmx[i] = dmx[i]
        packet = self.buildDMXHeader()
        packet.extend(plainDmx)
        self.__send(packet)

if __name__ == '__main__':
    artnet = ArtNet(broadcast='10.0.1.133')
    dmx = bytearray()
    fh = open("dmx.dat", 'r')
    for i in fh.readlines():
        dmx.append(int(i))
    artnet.sendToDmx(dmx)

    # load file
    # prepare to send

