import numpy as np


def exp_generator(env, intensity):
    mean = 1 / intensity
    while True:
        yield env.random.exponential(mean)


def uniform_generator(env, a=0.0, b=1.0):
    while True:
        yield env.random.uniform(a, b)


def static_generator(a):
    while True:
        yield a
