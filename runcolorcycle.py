#!/usr/bin/env python3
"""Sample script to run a few colour tests on the strip."""
import colorschemes

options = {
    'num_led': 200,
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
MY_CYCLE = colorschemes.Rainbow(num_steps_per_cycle=255, num_cycles=1,
                                **options)
MY_CYCLE.start()

# Five quick trips through the rainbow
print('Five quick trips through the rainbow')
MY_CYCLE = colorschemes.TheaterChase(pause_value=0.04, num_steps_per_cycle=35, num_cycles=5,
                                   **options)
MY_CYCLE.start()

print('Finished the test')
