from apa102 import Pixel
from PIL import Image
import time

def display_frames(fp, apa102_2d, brightness=100, frame_duration_s=0.2):
    width, height = apa102_2d.dimensions

    next_time = None
    frame = Image.open(fp)
    frame_i = 0
    while frame:
        render = frame.resize((width, height), Image.HAMMING).convert("RGB")
        for y in range(height):
            for x in range(width):
                r, g, b = render.getpixel((x, y))
                apa102_2d.putpixel((x, y), Pixel(r, g, b, brightness))

        if next_time is not None:
            time.sleep(next_time - time.perf_counter())
        else:
            next_time = time.perf_counter()
        next_time += frame_duration_s

        apa102_2d.show()

        frame_i += 1
        try:
            frame.seek(frame_i)
        except EOFError:
            break;

    frame.close()

