import numpy as np


def exp_generator(intensity):
    mean = 1 / intensity
    while True:
        yield np.random.exponential(mean)


gen = exp_generator(1)
for i in range(0, 100):
    print(gen.__next__())
