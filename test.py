from collections import deque


class A(object):
    def tmp(self):
        print("hello")


class B(A):
    def foo(self):
        self.tmp()


B().foo()
