import time
import ArtNet
import config

from libavg import Point2D


def clip_byte(value):
    return max(min(int(value), 255), 0)
    #val = int(value) & ~1 # random guess
    #return max(min(val, 254), 0)
    #return max(min(val, 254), 20) # TODO: why does it break on low values (e.g. 10)

class DmxLight(object):
    def __init__(self, dmx, start_channel, pos):
        self._dmx = dmx
        self._start_channel = start_channel
        self.pos = Point2D(pos)

    def _get_color(self, color):
        return self._dmx[self._start_channel + self._dmx_offsets[color]]

    def _set_color(self, color, value):
        dmx_pos = self._start_channel + self._dmx_offsets[color]
        self._dmx[dmx_pos] = clip_byte(value)

    for color in 'red', 'green', 'blue':
        locals()[color] = property(
                lambda self: self._get_color(color),
                lambda self, value, color=color: self._set_color(color, value))


class Dmx5Light(DmxLight):
    """ 5-channel dmx light"""
    _dmx_offsets = {'red': 1, 'green': 2, 'blue': 3}

class Dmx6Light(DmxLight):
    """ 6-channel dmx light"""
    _dmx_offsets = {'red': 0, 'green': 1, 'blue': 2}

class MainhallDmx(object):
    def __init__(self):
        self.dmx_server = ArtNet.ArtNet(broadcast = config.DMX_SERVER)
        self.dmx = bytearray([0] * 512)
        self.lights = [
                Dmx5Light(self.dmx, 0, (535, 249)),
                Dmx5Light(self.dmx, 5, (535, 328)),
                Dmx5Light(self.dmx, 10, (446, 250)),
                Dmx5Light(self.dmx, 15, (446, 330)),
                Dmx5Light(self.dmx, 20, (317, 251)),
                Dmx5Light(self.dmx, 25, (317, 300)),
                Dmx5Light(self.dmx, 30, (274, 278)),
                Dmx5Light(self.dmx, 35, (213, 278)),
                Dmx5Light(self.dmx, 40, (150, 281)),
                Dmx5Light(self.dmx, 45, (100, 291)),
                Dmx6Light(self.dmx, 100, (500, 270)),
                Dmx6Light(self.dmx, 106, (500, 305)),
                Dmx6Light(self.dmx, 112, (527, 310)),
                Dmx6Light(self.dmx, 118, (527, 270)),
                #Dmx1Light(self.dmx, 81, 317, (330,  9)),
                #Dmx1Light(self.dmx, 82, 330, (200,  9)),
                #Dmx1Light(self.dmx, 83, 460, (200,  9)),
                #Dmx1Light(self.dmx, 84, 446, (290,  9)),
                ]
        self.normalizeCoords()

    def normalizeCoords(self):
        min_x = min([light.pos.x for light in self.lights])
        max_x = max([light.pos.x for light in self.lights])
        min_y = min([light.pos.y for light in self.lights])
        max_y = max([light.pos.y for light in self.lights])
        if max_x == min_x:
            return
        if max_y == min_y:
            return
        factor = 1. / max((max_x-min_x), (max_y - min_y))
        for light in self.lights:
            light.pos -= Point2D(min_x, min_y)
            light.pos *= factor

    def sendToDmx(self):
        assert (len(self.dmx) == 512)
        self.dmx_server.sendToDmx(self.dmx)

