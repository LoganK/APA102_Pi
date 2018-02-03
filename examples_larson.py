#!/usr/bin/env python3
"""Classic Larson scanner in a tasteful red."""
from apa102 import APA102, Pixel
import argparse
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Display a larson scanner.')
    parser.add_argument('num_led', type=int, default=80, nargs='?',
                        help='The number of LEDs in the strip')
    parser.add_argument('mosi', type=int, default=10, nargs='?',
                        help='The pin for SPI MOSI. 10 corresponds to the Raspberry Pi hardware SPI.'
                        ' Set negative for console debug.')
    parser.add_argument('sclk', type=int, default=11, nargs='?',
                        help='The pin for SPI SCLK. 11 corresponds to the Raspberry Pi hardware SPI.')
    parser.add_argument('--duration', dest='duration_s', type=float, default=7,
                        help='How long the scanner should run in seconds.')
    args = parser.parse_args()

    with APA102(args.num_led, mosi=args.mosi, sclk=args.sclk) as strip:
        larson1 = create_larson(strip, 0, strip.num_led // 2 - 1)
        larson2 = create_larson(strip, strip.num_led // 2, strip.num_led  - 1)

        # Run for 10 seconds
        end_time = time.time() + args.duration_s
        while time.time() < end_time:
            strip.blank()
            larson1()
            larson2()
            strip.show()
            time.sleep(0.008)


