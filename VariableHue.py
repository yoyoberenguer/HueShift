"""
This code generates a hue* cyclically rotated over time.

The original image is sliced into equal or near-equal size data chunks and pushed into
a multiprocessing queue in order to be processed simultaneously by designated number
of sub-process called <<listener>>. Those process are spawn at start and
run in the background, waiting for data to be pushed.
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

This algorithm is very effective for processing large images or very demanding calculation.
It can be adapted to Gaussian blur algorithm or other kernel calculations.

performance:
image size  5000x5000x32         24s   (16 process) -> 197 on a single thread.
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

"""

import pygame
import numpy
from numpy import putmask
import multiprocessing
from multiprocessing import Process, Queue, freeze_support
import hashlib
import colorsys
import time

__author__ = "Yoann Berenguer"
__copyright__ = "Copyright 2007."
__credits__ = ["Yoann Berenguer"]
__license__ = "MIT License"
__version__ = "1.0.0"
__maintainer__ = "Yoann Berenguer"
__email__ = "yoyoberenguer@hotmail.com"
__status__ = "Demo"


class Listener(Process):
    shift = 0

    def __init__(self, listener_name_, data_, out_, event_):
        super(Process, self).__init__()
        self.out_ = out_
        self.data = data_
        self.shift = Listener.shift
        self.listener_name = listener_name_
        self.event = event_
        self.stop = False

    def shift_hue(self, r, g, b):

        hue_ = pygame.Color(int(r), int(g), int(b)).hsva
        # shift the hue
        hue_ = ((hue_[0] * 0.0027) + self.shift, hue_[1] * 0.01, hue_[2] * 0.01)  # (1/360, 1/100, 1/100)
        rgb_color = colorsys.hsv_to_rgb(*(hue_[:3]))
        return rgb_color[0] * 255, rgb_color[1] * 255, rgb_color[2] * 255

    def shift_hue_loop(self, rgb_array):
        for x in range(rgb_array.shape[0]):
            for y in range(rgb_array.shape[1]):
                color_ = rgb_array[x, y][:3]
                hue_ = pygame.Color(int(color_[0]), int(color_[1]), int(color_[2])).hsva
                hue_ = ((hue_[0] * 0.0027) + self.shift, hue_[1] * 0.01, hue_[2] * 0.01)
                rgb_color = colorsys.hsv_to_rgb(*(hue_[:3]))
                rgb_array[x, y] = rgb_color[0] * 255, rgb_color[1] * 255, rgb_color[2] * 255
        return rgb_array

    def run(self):
        while not self.event.is_set():
            # if data is present in the list
            if self.data[self.listener_name] is not None:
                rgb_array = self.data[self.listener_name]

                vectorize_ = numpy.vectorize(self.shift_hue)
                source_array_ = vectorize_(rgb_array[:, :, 0],
                                           rgb_array[:, :, 1],
                                           rgb_array[:, :, 2])

                source_array_ = numpy.array(source_array_).transpose(1, 2, 0)

                # source_array_=self.shift_hue_algo(rgb_array)

                # Send the data throughout the QUEUE
                self.out_.put({self.listener_name: source_array_})
                # Delete the job from the list (self.data).
                # This will place the current process in idle
                self.data[self.listener_name] = None
                # print('Listener %s complete ' % self.listener_name)
                self.shift += 0.01
            # Minimize the CPU utilization while the process
            # is listening.
            time.sleep(0.005)
        print('Listener %s is dead.' % self.listener_name)


class SplitSurface:

    def __init__(self, process_: int, array_, queue, check_: bool = False):

        assert isinstance(process_, int), \
            'Expecting an int for argument process_, got %s ' % type(process_)
        assert isinstance(array_, numpy.ndarray), \
            'Expecting numpy.ndarray for argument array_, got %s ' % type(array_)
        assert isinstance(check_, bool), \
            'Expecting bool for argument check_, got %s ' % type(check_)

        self.process = process_  # Process number
        self.shape = array_.shape  # array shape
        self.col, self.row, self.c = tuple(self.shape)  # Columns, Rows, colors
        self.pixels = array_.size / self.c  # Pixels [w x h]
        self.size = array_.size  # Array size [w x h x colors]
        self.array = array_  # surface (numpy.array)
        self.queue = queue
        self.split_array = []
        # self.split()
        self.split_non_equal()

        # Checking hashes (input array & output)
        # Below works only if the array is rebuild
        # if check_:
        #    self.hash = hashlib.md5()
        #    self.hash.update(array_.copy('C'))
        #    self.hash_ = hashlib.md5()
        #    self.hash_.update(self.split_array.copy('C'))
        #    assert self.hash.hexdigest() == self.hash_.hexdigest(), \
        #        '\n[-] Secure hashes does not match.'

    def split_equal(self):
        # Split array into multiple sub-arrays of equal size.
        self.split_array = numpy.split(self.array, self.process)
        self.queue.put(self.split_array)

    def split_non_equal(self):
        # Split an array into multiple sub-arrays of equal or near-equal size.
        #  Does not raise an exception if an equal division cannot be made.
        split_ = numpy.array_split(self.array, self.process, 1)
        # self.split_array = numpy.vstack((split_[i] for i in range(self.process)))
        self.queue.put(split_)

    def split(self):

        split_array = []

        # chunk size (d_column, d_row) for a given number of process.
        d_column, d_row = self.col // self.process, self.row
        # cut chunks of data from the surface (numpy 3D array).
        print(d_column, d_row)
        split_size = 0
        # Summing the chunks and calculate the remainder if any.
        for i in range(self.process):
            split_array.append(self.array[0:d_row, i * d_column:i * d_column + d_column])
            split_size += split_array[i]

        remainder = int((self.pixels - self.process * d_column * d_row))

        # Remainder not null --> Adding the remainder to the last chunk
        # todo - we could also split the remainder into the number of process and split the value
        if remainder != 0:
            split_array[self.process - 1] = self.array[0:d_row,
                                            (self.process - 1) * d_column:(self.process - 1) * d_column + d_column + (
                                                        remainder // d_row)]

        self.queue.put(split_array)

        # rebuild complete array
        # self.split_array = numpy.hstack((split_array[i] for i in range(self.process)))
        # self.queue.put(self.split_array)


if __name__ == '__main__':
    freeze_support()
    # Map size
    SIZE = (200, 200)
    SCREENRECT = pygame.Rect((0, 0), SIZE)
    pygame.init()
    SCREEN = pygame.display.set_mode(SCREENRECT.size, pygame.RESIZABLE, 32)
    TEXTURE1 = pygame.image.load("Assets\\orange-hooded-gouldian-finch.jpg").convert()
    TEXTURE1 = pygame.transform.smoothscale(TEXTURE1, SIZE)

    array = pygame.surfarray.pixels3d(TEXTURE1)

    # Test for single thread
    def shift_hue_loop(rgb_array):
        for x in range(rgb_array.shape[0]):
            for y in range(rgb_array.shape[1]):
                color_ = rgb_array[x, y][:3]
                hue_ = pygame.Color(int(color_[0]), int(color_[1]), int(color_[2])).hsva
                hue_ = ((hue_[0] * 0.0027) + 0.01, hue_[1] * 0.01, hue_[2] * 0.01)
                rgb_color = colorsys.hsv_to_rgb(*(hue_[:3]))
                rgb_array[x, y] = rgb_color[0] * 255, rgb_color[1] * 255, rgb_color[2] * 255
        return rgb_array

    PROCESS = multiprocessing.cpu_count()

    QUEUE_OUT = multiprocessing.Queue()
    QUEUE_IN = multiprocessing.Queue()
    EVENT = multiprocessing.Event()

    MANAGER = multiprocessing.Manager()

    DATA = MANAGER.dict()

    SplitSurface(PROCESS, array, QUEUE_IN)
    new_array = QUEUE_IN.get()

    i = 0
    for array in new_array:
        DATA[i] = array
        i += 1

    t1 = time.time()
    for i in range(PROCESS):
        Listener.shift = 0.0
        Listener(i, DATA, QUEUE_OUT, EVENT).start()

    FRAME = 0
    clock = pygame.time.Clock()
    STOP_GAME = False
    PAUSE = False

    while not STOP_GAME:

        pygame.event.pump()

        while PAUSE:
            event = pygame.event.wait()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_PAUSE]:
                PAUSE = False
                pygame.event.clear()
                keys = None
            break

        for event in pygame.event.get():

            keys = pygame.key.get_pressed()

            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                print('Quitting')
                STOP_GAME = True

            elif event.type == pygame.MOUSEMOTION:
                MOUSE_POS = event.pos

            elif keys[pygame.K_PAUSE]:
                PAUSE = True
                print('Paused')

        t1 = time.time()

        # Push jobs into the Queue
        i = 0
        for array in new_array:
            DATA[i] = array
            i += 1

        temp = {}
        for i in range(PROCESS):
            for key, value in (QUEUE_OUT.get().items()):
                temp[str(key)] = value

        element = []
        for key, value in sorted(temp.items(), key=lambda item: (int(item[0]), item[1])):
            element.append(value)

        # uncomment below for for single thread testing
        # surface = pygame.surfarray.make_surface(shift_hue_loop(array))

        pygame.surfarray.blit_array(SCREEN, numpy.hstack(list(element)))
        # print('\n[+] time : ', time.time() - t1)

        pygame.display.flip()
        TIME_PASSED_SECONDS = clock.tick(350)
        FRAME += 1

    EVENT.set()

    pygame.quit()
