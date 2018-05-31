#!/usr/bin/env python3
"""Sample script to run a few colour tests on the strip."""
from apa102_2d import APA102_2D
import argparse
import image_util
import math
import time

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Display a larson scanner.')
    parser.add_argument('num_led', type=int, default=80, nargs='?',
                        help='The number of LEDs in the strip')
    parser.add_argument('mosi', type=int, default=10, nargs='?',
                        help='The pin for SPI MOSI. 10 corresponds to the Raspberry Pi hardware SPI.'
                        ' Set negative for console debug.')
    parser.add_argument('sclk', type=int, default=11, nargs='?',
                        help='The pin for SPI SCLK. 11 corresponds to the Raspberry Pi hardware SPI.')
    parser.add_argument('--image', nargs='+',
                        help='Controls which images to load.')
    args = parser.parse_args()

    print(args)
    width = int(math.sqrt(args.num_led))
    with APA102_2D(num_led=args.num_led,
                   led_order=[range(n, n+width) for n in range(0, args.num_led, width)],
                   mosi=args.mosi,
                   sclk=args.sclk) as apa:

        for image in args.image:
            for i in range(5):
                image_util.display_frames(image, apa)
                time.sleep(5)

            apa.clear_strip()
    

    print('Finished the test')

