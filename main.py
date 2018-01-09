import simpy


class HeaderException(Exception):
    pass


class Package(object):
    """
    package to be sent
    each package has a payload - which is the number of bytes with application information
    each package has at least one header (multiple headers may be stacked) - each header is a tuple of (size, data)
        where size is the number of bytes of this header and data is some data the header contains
        this can be used to encapsulate a frame in another one
    each package has a source - which is an unique identifier of a node in the system
    each package has a destination - which is an unique identifier of a node in the system
    """
    def __init__(self, payload, header, source, destination):
        self.payload = payload
        self.source = source
        self.destination = destination
        self.headers = []
        self.append_header(header)

    def peek_header(self):
        if self.headers.__len__() == 0:
            raise HeaderException(" ".join(str(self), "has no header"))
        return self.headers[self.headers.__len__() - 1]

    def pop_header(self):
        if self.headers.__len__() == 0:
            raise HeaderException(" ".join(str(self), "has no header"))
        return self.headers.pop()

    def append_header(self, header):
        # todo check header
        self.headers.append(header)
        return self

    def __len__(self):
        t_len = self.payload
        for header in self.headers:
            t_len += header[0]
        return t_len

    def __str__(self):
        return "Package: From %s to %s with size %d" % (str(self.source), str(self.destination), self.__len__())


class Node(object):

    def __init__(self, address):
        self.address = address

    def on_package_received(self, package, interface):
        raise NotImplementedError("You have to implement this")

    def push(self, package, interface):
        self.on_package_received(package, interface)


class NetworkEnvironment(simpy.Environment):
    pass


class Flow(Node):
    pass


class Sink(Node):
    pass


class Switch(Node):
    pass


tmp = Package(10, (0, 1), 1, 1)
print(tmp)
