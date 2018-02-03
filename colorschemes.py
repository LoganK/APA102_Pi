"""This module contains a few concrete colour cycles to play with"""

from math import ceil, floor, sqrt
from random import randint

from colorcycletemplate import ColorCycleTemplate
from apa102 import Pixel

class StrandTest(ColorCycleTemplate):
    """Runs a simple strand test (9 LEDs wander through the strip)."""

    color = None

    def init(self, strip, num_led):
        self.colors = [Pixel.RED, Pixel.GREEN, Pixel.BLUE]
        self.len = min(9, ceil(num_led / 10))

    def update(self, strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        # Cycle colors whenever we start a new cycle.
        if current_step == 0 and current_cycle != 0:
            self.colors = self.colors[1:] + self.colors[0:1]

        # Head is always the current item, tail is the left-most light (which
        # wraps around at the beginning).
        head = current_step
        tail = (current_step - self.len) % num_steps_per_cycle

        strip[head] = self.colors[0]  # Paint head
        if head != tail:
            strip[tail] = Pixel.BLACK

        return 1 # Repaint is necessary


class TheaterChase(ColorCycleTemplate):
    """Runs a 'marquee' effect around the strip."""
    def update(self, strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        # One cycle = One trip through the color wheel, 0..254
        # Few cycles = quick transition, lots of cycles = slow transition
        # Note: For a smooth transition between cycles, numStepsPerCycle must
        # be a multiple of 7
        start_index = current_step % 7 # One segment is 2 blank, and 5 filled
        color_index = strip.wheel(int(round(255/num_steps_per_cycle *
                                            current_step, 0)))
        for pixel in range(num_led):
            # Two LEDs out of 7 are blank. At each step, the blank
            # ones move one pixel ahead.
            if ((pixel+start_index) % 7 == 0) or ((pixel+start_index) % 7 == 1):
                strip.set_pixel_rgb(pixel, 0)
            else: strip.set_pixel_rgb(pixel, color_index)
        return 1


class RoundAndRound(ColorCycleTemplate):
    """Runs three LEDs around the strip."""

    def init(self, strip, num_led):
        strip.set_pixel_rgb(0, 0xFF0000)
        strip.set_pixel_rgb(1, 0xFF0000, 5) # Only 5% brightness
        strip.set_pixel_rgb(2, 0xFF0000)

    def update(self, strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        # Simple class to demonstrate the "rotate" method
        strip.rotate()
        return 1


class Solid(ColorCycleTemplate):
    """Paints the strip with one colour."""

    def init(self, strip, num_led):
        for led in range(0, num_led):
            strip.set_pixel_rgb(led,0xFFFFFF,15) # Paint 15% white

    def update(self, strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        # Do nothing: Init lit the strip, and update just keeps it this way
        return 0


class Rainbow(ColorCycleTemplate):
    """Paints a rainbow effect across the entire strip."""

    def update(self, strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        # One cycle = One trip through the color wheel, 0..254
        # Few cycles = quick transition, lots of cycles = slow transition
        # -> LED 0 goes from index 0 to 254 in numStepsPerCycle cycles.
        #     So it might have to step up more or less than one index
        #     depending on numStepsPerCycle.
        # -> The other LEDs go up to 254, then wrap around to zero and go up
        #     again until the last one is just below LED 0. This way, the
        #     strip always shows one full rainbow, regardless of the
        #     number of LEDs
        scale_factor = 255 / num_led # Index change between two neighboring LEDs
        start_index = 255 / num_steps_per_cycle * current_step # LED 0
        for i in range(num_led):
            # Index of LED i, not rounded and not wrapped at 255
            led_index = start_index + i * scale_factor
            # Now rounded and wrapped
            led_index_rounded_wrapped = int(round(led_index, 0)) % 255
            # Get the actual color out of the wheel
            pixel_color = strip.wheel(led_index_rounded_wrapped)
            strip.set_pixel_rgb(i, pixel_color)
        return 1 # All pixels are set in the buffer, so repaint the strip now


def add_delay(delay_pct, *updaters):
    """A meta-updater that will delay an effect. Used by wrapping an updater:
        add_delay(0.1, create_solid(0, 10, Pixel.RED)) # Show red 10% into the cycle
    """

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        delay = round(delay_pct * num_steps_per_cycle)
        if current_step < delay:
            return 0
        return sum((u(strip, num_led, num_steps_per_cycle, current_step - delay, current_cycle)
                    for u in updaters))
    return update


def blank_updater(strip, num_led, num_steps_per_cycle, current_step,
          current_cycle):
    """A helper updater that simply clears the strip."""

    strip.blank()
    return 1 # Repaint


def create_solid(start, end, pixel):
    """A helper updater that simply sets a solid color."""

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        if current_step != 0:
            return 0
        for i in range(start, end+1):
            strip[i] = pixel
        return 1 # Repaint
    return update


def create_larson(start, end, width):
    """ Return a function that will update strip with the next Larson data.
    Params:
        start, end - Both inclusive.
    """
    b_step = ceil(100 // width)
    led = start - 1
    direction = 1
    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        nonlocal led, direction
        led += direction
        if led == end + width:
            direction = -1
            led = end
        if led == start - width:
            direction = 1
            led = start
        bright = 100
        for i in range(start, end+1):
            strip[i] = Pixel.BLACK
        for i in range(led, led + (-direction * width), -direction):
            if start <= i <= end:
                strip[i] = Pixel(255, 0, 0, bright)
            bright -= b_step

        return 1 # Repaint
    return update

def create_fire(start, end):
    """Return a fire updater."""

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        r, g, b = 255, 96, 12
        for i in range(start, end+1):
            flicker = randint(0, 40)
            strip[i] = Pixel(r-flicker, g-flicker, b-flicker, 100)
        return 1 # Repaint
    return update

def create_red_alert(start, end):
    """Return a rising red updater."""

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        brightness = round(100 * current_step / num_steps_per_cycle)
        lamp = Pixel(255, 0, 0, brightness)
        for i in range(start, end+1):
            strip[i] = lamp
        return 1 # Repaint
    return update

def create_swipe(start, end):
    """Return an updater that will shift all effects in, one pixel per cycle. Add
    this updater after other effects.
    Params:
        start, end - Inclusive ranges. Will swipe right to left if start > end.
    """

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        shift_max = abs(end-start)
        shift = shift_max-current_step
        if shift <= 0:
            return 0
        if start < end:
            for i in range(start, end+1):
                strip[i] = strip[i+shift] if i+shift <= end else Pixel.BLACK
        else:
            for i in range(start, end-1, -1):
                strip[i] = strip[i-shift] if i-shift >= end else Pixel.BLACK
        return 1 # Repaint
    return update

def create_morse(start, end, color, msg):
    """Crawl a Morse code message across the strand.
    Params:
      color - A Pixel to use as the color.
    """

    morse = {
        'A': '.-',
        'B': '-...',
        'C': '-.-.',
        'D': '-..',
        'E': '.',
        'F': '..-.',
        'G': '--.',
        'H': '....',
        'I': '..',
        'J': '.---',
        'K': '-.-',
        'L': '.-..',
        'M': '--',
        'N': '-.',
        'O': '---',
        'P': '.--.',
        'Q': '--.-',
        'R': '.-.',
        'S': '...',
        'T': '-',
        'U': '..-',
        'V': '...-',
        'W': '.--',
        'X': '-..-',
        'Y': '-.--',
        'Z': '--..',
        '1': '.----',
        '2': '..---',
        '3': '...--',
        '4': '....-',
        '5': '.....',
        '6': '-....',
        '7': '--...',
        '8': '---..',
        '9': '----.',
        '0': '-----',
        '.': '.-.-.-',
        ',': '--..--',
        ':': '---...',
        '!': '-.-.--',
        '?': '..--..',
        '\'': '.----.',
        '-': '-....-',
        '/': '-..-.',
        '@': '.--.-.',
        '=': '-...-',
        ' ': ' ',
        }
    dots = {
        '.': '.',
        '-': '...',
        ' ': ' ',
    }

    # Convert Morse to dots only.
    morse_lamp = dict([(k, '  '.join([dots[c] for c in morse[k]])) for k in morse])

    # Convert the message and space it out a bit more.
    msg_morse = '    '.join(morse_lamp[c] for c in msg.upper()) + '  ' * 15
    #print(msg_morse)

    msg_lamp = [color if c == '.' else Pixel.BLACK for c in msg_morse]

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        for i in range(start, end+1):
            strip[i] = msg_lamp[(i+current_step)%len(msg_lamp)]
        return 1 # Repaint
    return update


def create_lin_fade(start, end, hold_pct=0.1, direction=1):
    """A linear brightness fader.
    Params:
        hold_pct - (Range 0--1) The percent of the cycle to hold at the end brightness.
        direction - 1 to fade up, -1 to fade down
    """

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        last_step = num_steps_per_cycle - ceil(hold_pct * num_steps_per_cycle)
        if current_step > last_step:
            return 0
        brightness = round(100 * current_step / last_step)
        if direction != 1:
            # Fade down
            brightness = 100 - brightness
        for i in range(start, end+1):
            # Copy all the colors and change brightness.
            strip[i] = Pixel(*strip[i][0:3], brightness=brightness)
        return 1 # Repaint
    return update

def create_exp_fade(start, end, exp=0.5, hold_pct=0.1, direction=1):
    """An exponential brightness fader.
    Params:
        exp - The exponentiation. Lower numbers result in faster time to bright.
        hold_pct - (Range 0--1) The percent of the cycle to hold at the end brightness.
        direction - 1 to fade up, -1 to fade down
    """

    def update(strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        last_step = num_steps_per_cycle - ceil(hold_pct * num_steps_per_cycle)
        if current_step > last_step:
            return 0
        scale = 100 / (last_step**exp)
        brightness = floor(scale * (current_step**exp))
        if direction != 1:
            # Fade down
            brightness = 100 - brightness
        for i in range(start, end+1):
            # Copy all the colors and change brightness.
            strip[i] = Pixel(*strip[i][0:3], brightness=brightness)
        return 1 # Repaint
    return update
