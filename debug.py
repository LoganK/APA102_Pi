import functools
import sys
import time

_LED_START = 0b11100000
_BRIGHTNESS = 0b00011111
_LED_CHAR = '\''
_RESET_COLOR = '\x1b[0m'
_HIDE_CURSOR = '\x1b[?25l'
_SHOW_CURSOR = '\x1b[?25h'

def _cursor_left(n):
    return ('\x1b[' + str(n) + 'D') if n > 0 else ''
def _cursor_right(n):
    return ('\x1b[' + str(n) + 'C') if n > 0 else ''
def _cursor_down(n):
    return ('\x1b[' + str(n) + 'B') if n > 0 else ''
def _cursor_up(n):
    return ('\x1b[' + str(n) + 'A') if n > 0 else ''

# http://www.tldp.org/HOWTO/Bash-Prompt-HOWTO/x361.html
# Add some https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm
class DummySPI():
    def __init__(self, rgb_order):
        self.order = rgb_order

        # Current location of the cursor.
        self.x = 0
        self.y = 0

        # A map of physical index -> x, y (if configured).
        self.logical_map = dict()

        # The index of the next LED to receive a command.
        self.led_index = 0

    def setup_matrix(self, led_matrix):
        self.logical_map = dict()
        for y, row in enumerate(led_matrix):
            for x, phy in enumerate(row):
                if phy is not None:
                    self.logical_map[phy] = (x, y)

    @functools.lru_cache(maxsize=1024)
    def led_out(self, lamp):
        level = (lamp[0] & _BRIGHTNESS) / _BRIGHTNESS
        (r, g, b) = [round(level * lamp[n]) for n in self.order]
        return '\x1b[48;2;{};{};{}m{}'.format(r, g, b, _LED_CHAR)

    def write(self, byte_seq):
        # Black foreground so we can mark the LED without being too distracting.
        print('\x1b[38;2;0;0;0m', end='')

        # Process in 4-byte chunks as god intended.
        for cmd in list(zip(*[byte_seq[i::4] for i in range(4)])):
            buf = ''
            if cmd == (0x00, 0x00, 0x00, 0x00):
                self.led_index = 0
                if self.x != 0 or self.y != 0:
                    buf += _cursor_left(self.x) + _cursor_up(self.y)
                    self.x = 0
                    self.y = 0
            elif (cmd[0] & _LED_START) == _LED_START:
                next_x, next_y = self.logical_map.get(self.led_index, (self.x, self.y))
                if self.x < next_x:
                    buf += _cursor_right(next_x - self.x)
                elif self.x > next_x:
                    buf += _cursor_left(self.x - next_x)
                if self.y < next_y:
                    buf += _cursor_down(next_y - self.y)
                elif self.y > next_y:
                    buf += _cursor_up(self.y - next_y)
                buf += self.led_out(cmd)
                self.led_index += 1
                self.x = next_x + 1
                self.y = next_y
            print(buf, end='')

        print(_RESET_COLOR + _HIDE_CURSOR, end='', flush=True)

        # Slow down so we don't simply run at CPU speeds.
        time.sleep(0.005)

    def close(self):
        # Output a newline and reset to indicate this strand is done.
        print(_RESET_COLOR + _SHOW_CURSOR)
