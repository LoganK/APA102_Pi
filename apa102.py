"""This is the main driver module for APA102 LEDs"""
from math import ceil
from collections import namedtuple
import itertools

import debug

RGB_MAP = { 'rgb': [3, 2, 1], 'rbg': [3, 1, 2], 'grb': [2, 3, 1],
            'gbr': [2, 1, 3], 'brg': [1, 3, 2], 'bgr': [1, 2, 3] }

# Red, Green, Blue are supposed to be in the range 0--255. Brightness is in the
# range 0--100.
Pixel = namedtuple('Pixel', 'red green blue brightness')
Pixel.RED = Pixel(255, 0, 0, 100)
Pixel.YELLOW = Pixel(255, 255, 0, 100)
Pixel.GREEN = Pixel(0, 255, 0, 100)
Pixel.CYAN = Pixel(0, 255, 255, 100)
Pixel.BLUE = Pixel(0, 0, 255, 100)
Pixel.MAGENTA = Pixel(255, 0, 255, 100)
Pixel.WHITE = Pixel(255, 255, 255, 100)

class APA102Cmd:
  """Helper class to convert Pixel instance to an APA102 command.
  """
  LED_START = 0b11100000 # Three "1" bits, followed by 5 brightness bits
  BRIGHTNESS = 0b00011111

  def __init__(self, rgb_map, max_brightness):
    self.rgb_map = rgb_map
    self.max_brightness = max(max_brightness, APA102Cmd.BRIGHTNESS)

  def to_cmd(self, pixel):
    if not isinstance(pixel, Pixel):
      raise TypeError("expected Pixel")

    brightness = int(ceil(pixel.brightness*self.max_brightness/100.0))

    # LED startframe is three "1" bits, followed by 5 brightness bits
    ledstart = (brightness & 0b00011111) | self.LED_START

    cmd = [ledstart, 0, 0, 0]

    # Note that rgb_map is 1-indexed for historial reasons, but is convenient here.
    cmd[self.rgb_map[0]] = pixel.red
    cmd[self.rgb_map[1]] = pixel.green
    cmd[self.rgb_map[2]] = pixel.blue

    return cmd


class APA102:
    """
    Driver for APA102 LEDS (aka "DotStar").

    (c) Martin Erzberger 2016-2017

    Public methods are:
     - set_pixel
     - set_pixel_rgb
     - show
     - clear_strip
     - cleanup

    Helper methods for color manipulation are:
     - combine_color
     - wheel

    The rest of the methods are used internally and should not be used by the
    user of the library.

    Very brief overview of APA102: An APA102 LED is addressed with SPI. The bits
    are shifted in one by one, starting with the least significant bit.

    An LED usually just forwards everything that is sent to its data-in to
    data-out. While doing this, it remembers its own color and keeps glowing
    with that color as long as there is power.

    An LED can be switched to not forward the data, but instead use the data
    to change it's own color. This is done by sending (at least) 32 bits of
    zeroes to data-in. The LED then accepts the next correct 32 bit LED
    frame (with color information) as its new color setting.

    After having received the 32 bit color frame, the LED changes color,
    and then resumes to just copying data-in to data-out.

    The really clever bit is this: While receiving the 32 bit LED frame,
    the LED sends zeroes on its data-out line. Because a color frame is
    32 bits, the LED sends 32 bits of zeroes to the next LED.
    As we have seen above, this means that the next LED is now ready
    to accept a color frame and update its color.

    So that's really the entire protocol:
    - Start by sending 32 bits of zeroes. This prepares LED 1 to update
      its color.
    - Send color information one by one, starting with the color for LED 1,
      then LED 2 etc.
    - Finish off by cycling the clock line a few times to get all data
      to the very last LED on the strip

    The last step is necessary, because each LED delays forwarding the data
    a bit. Imagine ten people in a row. When you yell the last color
    information, i.e. the one for person ten, to the first person in
    the line, then you are not finished yet. Person one has to turn around
    and yell it to person 2, and so on. So it takes ten additional "dummy"
    cycles until person ten knows the color. When you look closer,
    you will see that not even person 9 knows its own color yet. This
    information is still with person 2. Essentially the driver sends additional
    zeroes to LED 1 as long as it takes for the last color frame to make it
    down the line to the last LED.

    Params:
      led_order - If set, allow the use of a logical order that doesn't match
        the physical strip given as a sequence of (first, last) ranges. As a
        compex example, if your strips were connected as:
        5-6-7-8-0-1-2-3-12-11-10-9
        then you could set led_order=((5, 8), (0, 3), (12, 9))
        Tip: runcolorcycle.py can be useful to verify you have these values correct.
    """
    def __init__(self,
                 num_led,
                 global_brightness=100,
                 order='rgb',
                 mosi=10,
                 sclk=11,
                 max_speed_hz=8000000,
                 led_order=None):
        """Initializes the library."""

        rgb_map = RGB_MAP[order.lower()]
        self.pixel_cmd = APA102Cmd(rgb_map, global_brightness)
        self.leds = [Pixel(0, 0, 0, 0) for n in range(num_led)]
        self.led_order = led_order
        self._assert_led_order()

        if mosi is None: # Debug output
            # Reset leds_seq so the terminal output makes sense.
            self.led_order = None
            self.spi = debug.DummySPI(rgb_map)
        else:
            import Adafruit_GPIO.SPI as SPI
            # MOSI 10 and SCLK 11 is hardware SPI, which needs to be set-up differently
            if mosi == 10 and sclk == 11:
                self.spi = SPI.SpiDev(0, 0, max_speed_hz) # Bus 0, chip select 0
            else:
                import Adafruit_GPIO as GPIO
                self.spi = SPI.BitBang(GPIO.get_platform_gpio(), sclk, mosi)

    def _assert_led_order(self):
        """Raise a ValueError if the given led_order isn't correct."""

        found = set(self.order_iter())
        need = set(range(len(self.leds)))
        if found != need:
            raise ValueError('led_order has gap and/or extra: {}'.format(need.symmetric_difference(found)))

    def clock_start_frame(self):
        """Sends a start frame to the LED strip.

        This method clocks out a start frame, telling the receiving LED
        that it must update its own color now.
        """
        self.spi.write([0] * 4)  # Start frame, 32 zero bits


    def clock_end_frame(self):
        """Sends an end frame to the LED strip.

        As explained above, dummy data must be sent after the last real colour
        information so that all of the data can reach its destination down the line.
        The delay is not as bad as with the human example above.
        It is only 1/2 bit per LED. This is because the SPI clock line
        needs to be inverted.

        Say a bit is ready on the SPI data line. The sender communicates
        this by toggling the clock line. The bit is read by the LED
        and immediately forwarded to the output data line. When the clock goes
        down again on the input side, the LED will toggle the clock up
        on the output to tell the next LED that the bit is ready.

        After one LED the clock is inverted, and after two LEDs it is in sync
        again, but one cycle behind. Therefore, for every two LEDs, one bit
        of delay gets accumulated. For 300 LEDs, 150 additional bits must be fed to
        the input of LED one so that the data can reach the last LED.

        Ultimately, we need to send additional numLEDs/2 arbitrary data bits,
        in order to trigger numLEDs/2 additional clock changes. This driver
        sends zeroes, which has the benefit of getting LED one partially or
        fully ready for the next update to the strip. An optimized version
        of the driver could omit the "clockStartFrame" method if enough zeroes have
        been sent as part of "clockEndFrame".
        """
        # Round up num_led/2 bits (or num_led/16 bytes)
        self.spi.write([0x00] * ceil(self.num_led / 16))


    def clear_strip(self):
        """ Turns off the strip and shows the result right away."""
        self.leds = [Pixel(0, 0, 0, 0) for n in range(len(self.leds))]
        self.show()

    @property
    def num_led(self):
      return len(self.leds)


    def __getitem__(self, key):
        return self.leds[key]


    def __setitem__(self, key, item):
        """ Allows for setting lights using array syntax:
        strip[12] = Pixel(255, 255, 0, 50) # 50% Brightness yellow
        or
        strip[12] = (255, 255, 0) # 100% Brightness yellow
        """
        if isinstance(item, Pixel):
            self.leds[key] = item
        elif len(item) == 4:
            self.leds[key] = Pixel(*item)
        elif len(item) == 3:
            self.leds[key] = Pixel(*item, brightness=100)
        else:
            raise ValueError('unknown type for Pixel: {}'.format(item))


    def set_pixel(self, led_num, red, green, blue, bright_percent=100):
        """Sets the color of one pixel in the LED stripe.

        The changed pixel is not shown yet on the Stripe, it is only
        written to the pixel buffer. Colors are passed individually.
        If brightness is not set the global brightness setting is used.
        """
        if led_num < 0 or led_num >= self.num_led:
            raise ValueError('attempt to set invalid LED: {}'.format(led_num))

        self.leds[led_num] = Pixel(red, green, blue, bright_percent)

    def set_pixel_rgb(self, led_num, rgb_color, bright_percent=100):
        """Sets the color of one pixel in the LED stripe.

        The changed pixel is not shown yet on the Stripe, it is only
        written to the pixel buffer.
        Colors are passed combined (3 bytes concatenated)
        If brightness is not set the global brightness setting is used.
        """
        self.set_pixel(led_num, (rgb_color & 0xFF0000) >> 16,
                       (rgb_color & 0x00FF00) >> 8, rgb_color & 0x0000FF,
                        bright_percent)


    def rotate(self, positions=1):
        """ Rotate the LEDs by the specified number of positions.

        Treating the internal LED array as a circular buffer, rotate it by
        the specified number of positions. The number could be negative,
        which means rotating in the opposite direction.
        """
        cutoff = positions % self.num_led
        self.leds = self.leds[cutoff:] + self.leds[:cutoff]


    def order_iter(self):
        """Convert a user sequence of led_order tuples to a linear order."""

        if self.led_order is None:
            return range(self.num_led)

        order = []
        for s in led_order:
            if s[0] < s[1]:
                order.append(range(s[0], s[1] + 1, 1))
            else:
                order.append(range(s[1], s[0] - 1, -1))

        return itertools.chain(*order)

    def show(self):
        """Sends the content of the pixel buffer to the strip.

        Todo: More than 1024 LEDs requires more than one xfer operation.
        """
        self.clock_start_frame()
        # SPI takes up to 4096 Integers. So we are fine for up to 1024 LEDs.
        cmds = []
        for led_i in self.order_iter():
            cmds.extend(self.pixel_cmd.to_cmd(self.leds[led_i]))
        self.spi.write(cmds)
        self.clock_end_frame()


    def cleanup(self):
        """Release the SPI device; Call this method at the end"""

        self.spi.close()  # Close SPI port

    @staticmethod
    def combine_color(red, green, blue):
        """Make one 3*8 byte color value."""

        return (red << 16) + (green << 8) + blue


    def wheel(self, wheel_pos):
        """Get a color from a color wheel; Green -> Red -> Blue -> Green"""

        if wheel_pos > 255:
            wheel_pos = 255 # Safeguard
        if wheel_pos <= 85:  # Green -> Red
            return self.combine_color(wheel_pos * 3, 255 - wheel_pos * 3, 0)
        if wheel_pos <= 170:  # Red -> Blue
            wheel_pos -= 85
            return self.combine_color(255 - wheel_pos * 3, 0, wheel_pos * 3)
        # Blue -> Green
        wheel_pos -= 170
        return self.combine_color(0, wheel_pos * 3, 255 - wheel_pos * 3)


    def dump_array(self):
        """For debug purposes: Dump the LED array onto the console."""

        print(self.leds)
