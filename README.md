# Hue

WIKIPEDIA

Hue is one of the main properties (called color appearance parameters) of a color, defined technically (in the CIECAM02 model), as "the degree to which a stimulus can be described as similar to or different from stimuli that are described as red, green, blue, and yellow",(which in certain theories of color vision are called unique hues). 
Hue can typically be represented quantitatively by a single number, often corresponding to an angular position around a central or neutral point or axis on a colorspace coordinate diagram (such as a chromaticity diagram) or color wheel, or by its dominant wavelength or that of its complementary color. The other color appearance parameters are colorfulness, saturation (also known as intensity or chroma), lightness, and brightness.
Usually, colors with the same hue are distinguished with adjectives referring to their lightness or colorfulness, such as with "light blue", "pastel blue", "vivid blue". Exceptions include brown, which is a dark orange

![alt text](https://github.com/yoyoberenguer/HueShift/blob/master/hue1.png)

# Hue shifting 
Python Parallel Processing (data processing with fast hue shifting example)

This code generates a hue* cyclically rotated over time.

![alt text](https://github.com/yoyoberenguer/HueShift/blob/master/Hue.png)

The original image is sliced into equal or near-equal size data chunks and pushed into
a multiprocessing queue in order to be processed simultaneously by designated number
of sub-process called "listener". 
Those process are spawn at start and run in the background, waiting for data to be pushed.
When a job is complete, process are becoming idle until another job is pushed into the queue.
When all image portions have been processed (Queue empty), the image reconstruction is taking place.

By default, the number of process will be equivalent to the number of cpu's core (or cpu thread).
This value can be updated manually, but I don't recommend using 3 times more process than you cpu
is capable of handling. This is particularly true in environment where CPU power is needed for production tasks.
Spawning too many process at once will lag the system in its routine tasks and the whole system may become
momentarily unresponsive.

The hue method is not fully optimised and can of course be improve,
it just serve the purpose of the demonstration.

This algorithm was originally developed for a 2D video game to boost the processing time
and create real time rendering effects.

It is very effective for processing large images and can be adapted for Gaussian blur algorithm or other kernel calculations.

performance:
image size  5000x5000x32         24s   (16 process) -> 197s for a single thread.

            1280x1024x32         1.2s  (16 process) -> 10.5s single thread
            
            640x480x32           0.27s (16 process) -> 2.5s single thread
            
            200x200x32           40ms  (16 process) -> 325ms single thread

--------------------------------------------------------------------------------------------------------------------

This code comes with a MIT license.

Copyright (c) 2018 Yoann Berenguer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

Please acknowledge and give reference if using the source code for your project

--------------------------------------------------------------------------------------------------------------------
