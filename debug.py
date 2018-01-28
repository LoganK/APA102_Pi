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

    def write(self, byte_seq):
        # Process in 4-byte chunks as god intended.
        for x in list(zip(*[byte_seq[i::4] for i in range(4)])):
            if x == (0x00, 0x00, 0x00, 0x00):
                print('\r', end='')
            elif (x[0] & DummySPI.LED_START) == DummySPI.LED_START:
                level = (x[0] & DummySPI.BRIGHTNESS) / DummySPI.BRIGHTNESS
                (r, g, b) = [round(level * x[n]) for n in self.order]
                print('\x1b[48;2;{};{};{}m '.format(r, g, b), end='')

        # Disable the blinking cursor.
        print(DummySPI.RESET_COLOR + DummySPI.HIDE_CURSOR, end='', flush=True)

        # Slow down so we don't simply run at CPU speeds.
        time.sleep(0.001)

    def close(self):
        # Output a newline and reset to indicate this strand is done.
        print(DummySPI.RESET_COLOR + DummySPI.SHOW_CURSOR)
