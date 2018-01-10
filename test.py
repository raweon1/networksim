from collections import deque


class A(object):
    def __init__(self):
        print("Hello world")

class B(object):
    def __init__(self):
        print("Magic")


def foo(cls):
    return cls()


tmp = foo(A)
tmp2 = foo(A)
print(tmp == tmp2)
foo(B)
