import functools
import sys
import time

class DummySPI():
    LED_START = 0b11100000
    BRIGHTNESS = 0b00011111
    RESET_COLOR = '\x1b[0m'
    HIDE_CURSOR = '\x1b[?25l'
    SHOW_CURSOR = '\x1b[?25h'

    def __init__(self, rgb_order):
        self.order = rgb_order

    @functools.lru_cache(maxsize=1024)
    def led_out(self, lamp):
        level = (lamp[0] & DummySPI.BRIGHTNESS) / DummySPI.BRIGHTNESS
        (r, g, b) = [round(level * lamp[n]) for n in self.order]
        return '\x1b[48;2;{};{};{}m '.format(r, g, b)

    def write(self, byte_seq):
        # Process in 4-byte chunks as god intended.
        buf = ''
        for x in list(zip(*[byte_seq[i::4] for i in range(4)])):
            if x == (0x00, 0x00, 0x00, 0x00):
                buf += '\r'
            elif (x[0] & DummySPI.LED_START) == DummySPI.LED_START:
                buf += self.led_out(x)

        print(buf + DummySPI.RESET_COLOR + DummySPI.HIDE_CURSOR, end='', flush=True)

        # Slow down so we don't simply run at CPU speeds.
        time.sleep(0.005)

    def close(self):
        # Output a newline and reset to indicate this strand is done.
        print(DummySPI.RESET_COLOR + DummySPI.SHOW_CURSOR)
