#!/usr/bin/env python3
"""Ultra simple sample on how to use the library"""
from apa102 import APA102, Pixel
import time

# Initialize the library and the strip
strip = APA102(num_led=80, global_brightness=20, mosi = 10, sclk = 11,
                      order='rbg')

# Turn off all pixels (sometimes a few light up when the strip gets power)
strip.clear_strip()

# Prepare a few individual pixels through the various APIs.
strip[0] = (255, 0, 0) # Red
strip[12] = Pixel.BLUE
strip[24] = Pixel(red=0xFF, green=0xFF, blue=0xFF, brightness=100) # White
strip[36] = (255, 255, 0, 100) # Yellow
strip.set_pixel_rgb(40, 0x00FF00) # Green

# Copy the buffer to the Strip (i.e. show the prepared pixels)
strip.show()

# Wait a few Seconds, to check the result
time.sleep(20)

# Clear the strip and shut down
strip.clear_strip()
strip.cleanup()


