#!/usr/bin/env python3
"""Classic Larson scanner in a tasteful red."""
from apa102 import APA102, Pixel
from math import ceil
import time

def create_larson(strip, start, end):
    """ Return a function that will update strip with the next Larson data.
    Params:
        start, end - Both inclusive.
    """
    width = min(8, ceil(strip.num_led / 10))
    b_step = ceil(100 // width)
    led = start - 1
    direction = 1
    def next():
        nonlocal width, b_step, led, direction
        led += direction
        if led == end + width:
            direction = -1
            led = end
        if led == start - width:
            direction = 1
            led = start
        bright = 100
        for i in range(led, led + (-direction * width), -direction):
            if start <= i <= end:
                strip[i] = Pixel(255, 0, 0, bright)
            bright -= b_step
    return next

with APA102(num_led=80, mosi = None, sclk = 11) as strip:
    larson1 = create_larson(strip, 0, strip.num_led // 2 - 1)
    larson2 = create_larson(strip, strip.num_led // 2, strip.num_led  - 1)

    # Run for 10 seconds
    end_time = time.time() + 7
    while time.time() < end_time:
        strip.blank()
        larson1()
        larson2()
        strip.show()
        time.sleep(0.008)


