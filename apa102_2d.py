from apa102 import APA102
import debug
import logging

__logger = logging.getLogger(__name__)

class APA102_2D(APA102):
    """An APA102 driver that focuses more on 2D arrangements."""

    def __init__(self, led_order=None, **kwargs):
        """Initializes the library.

        Params:
          led_order - If set, allow the use of a logical order that doesn't
            match the physical strip given as a 2D matrix of light orders
            referenced from the upper-left corner. For example, a 3x3 grid set
            up in zig-zag order:
            0-1-2
            5-4-3
            6-7-8
            could be described as [[0, 1, 2], [5, 4, 3], [6, 7, 8]]. For larger
            grids, iterables are also supported ([range(0, 3), range(5, 2, -1), range(6, 9])
        """
 
        # Linearize the order so that we may re-use the underlying LED count tests.
        linear_order = [i for row in led_order for i in row]

        APA102.__init__(self, led_order=linear_order, **kwargs)

        # Convert to a simple rectangle and save the dimensions for reference.
        width = max([len(row) for row in led_order])
        height = len(led_order)
        self.dimensions = (width, height)
        def fixed_row(r):
            return list(r) + ([None] * (width - len(r)))
        self.led_matrix = [fixed_row(r) for r in led_order]

        if isinstance(self.spi, debug.DummySPI):
            self.spi.setup_matrix(self.led_matrix)

    def putpixel(self, xy, item):
        """Set the pixel at (x, y) to item."""

        index = None
        try:
            index = self.led_matrix[xy[1]][xy[0]]
        except IndexError:
            pass

        if index is None:
            __logger.warning(f'Attempt to set invalid location {xy}')

        self[index] = item

    def getpixel(self, xy, item):
        """Gets the pixel at (x, y)."""

        index = None
        try:
            index = self.led_matrix[xy[1]][xy[0]]
        except IndexError:
            pass

        if index is None:
            __logger.warning(f'Attempt to get invalid location {xy}')

        return self[index]
