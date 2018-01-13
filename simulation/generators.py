import numpy as np


def exp_generator(intensity):
    mean = 1 / intensity
    while True:
        yield np.random.exponential(mean)


def uniform_generator(a=0.0, b=1.0):
    while True:
        yield np.random.uniform(a, b)


def static_generator(a):
    while True:
        yield a
