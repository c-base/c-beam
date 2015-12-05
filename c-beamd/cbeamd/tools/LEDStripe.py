import config
import time

class LED:
    red = 0x00
    green = 0x00
    blue = 0x00

    def set_black(self):
        red = 0x00
        green = 0x00
        blue = 0x00

    def set_white(self):
        red = 0xFF
        green = 0xFF
        blue = 0xFF

    def set_red(self):
        red = 0xFF
        green = 0x00
        blue = 0x00

    def set_green(self):
        red = 0x00
        green = 0xFF
        blue = 0x00

    def set_blue(self):
        red = 0x00
        green = 0x00
        blue = 0xFF

    def __str__():
        return '%02x%02x%02x' % (red, green, blue)

class LEDStripe:
    leds = [LED() for e in range(0,config.LEDS_PER_STRIPE)]
    #leds = [LED()] * config.LEDS_PER_STRIPE
    is_reversed = False

    def __init__(self, is_reversed=False):
        self.is_reversed = is_reversed
        pass

    def to_bgr(self):
        if self.is_reversed:
            #return [(led.blue, led.green, led.red) for led in reversed(self.leds)]
            return [num for elem in [(led.blue, led.green, led.red) for led in reversed(self.leds)] for num in elem]
        else:
            #return [(led.blue, led.green, led.red) for led in self.leds]
            return [num for elem in [(led.blue, led.green, led.red) for led in self.leds] for num in elem]

    #def from_bgr(self, bgr):
        #if self.is_reversed:

    def rotate_left(self):
        self.leds = self.leds[1:] + self.leds[:1]

    def rotate_right(self):
        self.leds = self.leds[-1:] + self.leds[:-1]

    def to_rgb_list():
        pass


class LEDFrame:
    ledstripes = [LEDStripe() for e in range(0,config.LEDSTRIPES)]

    def __init__(self):
        self.ledstripes[1].is_reversed = True
        self.ledstripes[3].is_reversed = True

    def rotate_right(self):
        for stripe in self.ledstripes:
            stripe.rotate_right()

    def rotate_test(self):
        for x in range(0,128):
            for stripe in self.ledstripes:
                stripe.rotate_right()
            print self.current_buffer()
            time.sleep(0.1)

    def red_dot(self):
        for stripe in self.ledstripes:
            #for led in stripe.leds:
            #    led.set_black()
            for x in range(0,5):
                #stripe.leds[x].set_red()
                stripe.leds[x].red = 0xFF

    def red_dots(self):
        for stripe in self.ledstripes:
            for led in stripe.leds:
                led.set_black()
            for (x, led) in enumerate(stripe.leds):
                print x
                if x % 16 < 8:
                    led.set_red()



    def current_buffer(self):
        vec = [stripe.to_bgr() for stripe in self.ledstripes]
        return [num for elem in vec for num in elem]+[0,0,0,0,0,0,0,0,0,0,0,0]
        #return [num for elem in vec for num in elem]


