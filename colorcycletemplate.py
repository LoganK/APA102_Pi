"""The module contains templates for colour cycles"""
import time
import apa102

class ColorCycleTemplate:
    """This class is the basis of all color cycles.

    A specific color cycle must subclass this template, and implement at least the
    'update' method.

       Params:
         mosi, sclk - Hardware SPI uses BCM 10 & 11. Change these values for
           bit bang mode. MOSI = 23, SCLK = 24 for Pimoroni Phat Beat or Blinkt!
    """
    def __init__(self,
                 num_led,
                 pause_value = 0,
                 num_steps_per_cycle = 100,
                 num_cycles = -1,
                 global_brightness = 100,
                 order = 'rbg',
                 mosi = 10, sclk = 11):
        self.num_led = num_led # The number of LEDs in the strip
        self.pause_value = pause_value # How long to pause between two runs
        self.num_steps_per_cycle = num_steps_per_cycle # Steps in one cycle.
        self.num_cycles = num_cycles # How many times will the program run
        self.global_brightness = global_brightness # Brightness of the strip
        self.order = order # Strip colour ordering
        self.mosi = mosi
        self.sclk = sclk
        self.updaters = []

    def init(self, strip, num_led):
        """This method is called to initialize a color program.

        The default does nothing. A particular subclass could setup
        variables, or even light the strip in an initial color.
        """
        pass

    def shutdown(self, strip, num_led):
        """This method is called before exiting.

        The default does nothing
        """
        pass

    def update(self, strip, num_led, num_steps_per_cycle, current_step,
               current_cycle):
        """This method paints one subcycle. It must be implemented.

        current_step:  This goes from zero to numStepsPerCycle-1, and then
          back to zero. It is up to the subclass to define what is done in
          one cycle. One cycle could be one pass through the rainbow.
          Or it could be one pixel wandering through the entire strip
          (so for this case, the numStepsPerCycle should be equal to numLEDs).
        current_cycle: Starts with zero, and goes up by one whenever a full
          cycle has completed.
        """

        raise NotImplementedError("Please implement the update() method")


    def append_updater(self, updater):
        """This method appends an update function that works identically to update."""

        self.updaters.append(updater)


    def cleanup(self, strip):
        """Cleanup method."""
        self.shutdown(strip, self.num_led)
        strip.clear_strip()
        strip.cleanup()


    def start(self):
        """This method does the actual work."""

        # If there are no updaters, then revert to the old inheritence-based behavior.
        if len(self.updaters) == 0:
            self.updaters.append(self.update)

        try:
            strip = apa102.APA102(num_led=self.num_led,
                                  global_brightness=self.global_brightness,
                                  mosi = self.mosi, sclk = self.sclk,
                                  order=self.order) # Initialize the strip
            strip.clear_strip()
            self.init(strip, self.num_led) # Call the subclasses init method
            strip.show()
            current_cycle = 0
            next_time = time.time()
            while True:  # Loop forever
                for current_step in range (self.num_steps_per_cycle):
                    need_repaint = sum((
                        update(strip, self.num_led, self.num_steps_per_cycle,
                               current_step, current_cycle)
                        for update in self.updaters))
                    time.sleep(max(0, next_time-time.time()))
                    next_time += self.pause_value
                    if need_repaint:
                        strip.show() # repaint if required
                time.sleep(max(0, next_time-time.time())) # Final hold
                current_cycle += 1
                if self.num_cycles != -1:
                    if current_cycle >= self.num_cycles:
                        break
            # Finished, cleanup everything
            self.cleanup(strip)

        except KeyboardInterrupt:  # Ctrl-C can halt the light program
            print('Interrupted...')
            self.cleanup(strip)
            raise
