#!/usr/bin/env python3
"""Sample script to run a few colour tests on the strip."""
from apa102 import Pixel
import argparse
from colorcycletemplate import ColorCycleTemplate
import colorschemes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Display a larson scanner.')
    parser.add_argument('num_led', type=int, default=80, nargs='?',
                        help='The number of LEDs in the strip')
    parser.add_argument('mosi', type=int, default=10, nargs='?',
                        help='The pin for SPI MOSI. 10 corresponds to the Raspberry Pi hardware SPI.'
                        ' Set negative for console debug.')
    parser.add_argument('sclk', type=int, default=11, nargs='?',
                        help='The pin for SPI SCLK. 11 corresponds to the Raspberry Pi hardware SPI.')
    args = parser.parse_args()

    options = {
        'num_led': args.num_led,
        'mosi': args.mosi,
        'sclk': args.sclk,
    }

    # One Cycle with one step and a pause of theee seconds. Hence three seconds of white light
    print('Three Seconds of white light')
    MY_CYCLE = colorschemes.Solid(pause_value=3, num_steps_per_cycle=1, num_cycles=1,
                                  **options)
    MY_CYCLE.start()

    # Go twice around the clock
    print('Go twice around the clock')
    MY_CYCLE = colorschemes.RoundAndRound(num_steps_per_cycle=options['num_led'], num_cycles=2,
                                          **options)
    MY_CYCLE.start()

    # One cycle of red, green and blue each
    print('One strandtest of red, green and blue each')
    MY_CYCLE = colorschemes.StrandTest(num_steps_per_cycle=options['num_led'], num_cycles=3,
                                       **options)
    MY_CYCLE.start()

    # One slow trip through the rainbow
    print('One slow trip through the rainbow')
    MY_CYCLE = ColorCycleTemplate(num_steps_per_cycle=255, num_cycles=1,
                                  **options)
    rainbow = colorschemes.Rainbow(**options)
    MY_CYCLE.append_updater(rainbow.update)
    MY_CYCLE.append_updater(colorschemes.create_swipe(args.num_led-1, 0))
    MY_CYCLE.start()

    # Five quick trips through the rainbow
    print('Five quick trips through the rainbow')
    MY_CYCLE = colorschemes.TheaterChase(pause_value=0.04, num_steps_per_cycle=35, num_cycles=5,
                                       **options)
    MY_CYCLE.start()

    print('A Larson Scanner, a fire, and red alert')
    MY_CYCLE = ColorCycleTemplate(pause_value=0.02, num_steps_per_cycle=60, num_cycles=5,
                                  **options)
    MY_CYCLE.append_updater(colorschemes.blank_updater) # The scanners don't assume blank-to-start
    num_updaters = 3
    sec_width = args.num_led // num_updaters
    sec_ranges = list(zip(range(0, args.num_led, sec_width), range(sec_width-1, args.num_led, sec_width)))
    sec_ranges[-1] = (sec_ranges[-1][0], args.num_led-1) # Make sure we get them all
    MY_CYCLE.append_updater(colorschemes.create_larson(*sec_ranges.pop(0), width=8))
    MY_CYCLE.append_updater(colorschemes.create_fire(*sec_ranges.pop(0)))
    MY_CYCLE.append_updater(colorschemes.create_red_alert(*sec_ranges.pop(0)))
    MY_CYCLE.start()

    print('Morse codes')
    MY_CYCLE = ColorCycleTemplate(pause_value=0.2, num_steps_per_cycle=60, num_cycles=2,
                                  **options)
    MY_CYCLE.append_updater(colorschemes.create_morse(0, args.num_led-1, (153, 23, 255), 'pfy!'))
    MY_CYCLE.start()

    print('Finished the test')
