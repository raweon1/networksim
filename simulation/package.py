class Package(object):
    """
    package to be sent
    each package has a payload - which is the number of bytes with application information
    each package has at least one header (multiple headers may be stacked) - each header is a tuple of (size, data)
        where size is the number of bytes of this header and data is some data the header contains
        this can be used to encapsulate a frame in another one
    each package has a source - which is an unique identifier of a node in the system
    each package has a destination - which is an unique identifier of a node in the system
    each package has a priority
    each package has an automatically generated id
    """
    id = 1

    def __init__(self, source, destination, payload, priority=20, header=(26, "Ethernet_Frame_Header")):
        self.id = Package.id
        Package.id += 1
        self.payload = payload
        self.source = source
        self.destination = destination
        self.headers = []
        self.append_header(header)
        self.priority = priority

    def on_hop(self, sender, receiver):
        pass

    def on_destination_reached(self, node):
        pass

    def peek_header(self):
        if self.headers.__len__() == 0:
            raise HeaderException("%s has no header" % str(self))
        return self.headers[self.headers.__len__() - 1]

    def pop_header(self):
        if self.headers.__len__() == 0:
            raise HeaderException("%s has no header" % str(self))
        return self.headers.pop()

    def append_header(self, header):
        self.headers.append(header)
        return self

    def __len__(self):
        t_len = self.payload
        for header in self.headers:
            t_len += header[0]
        return t_len

    def __str__(self):
        return "Package(%d): (source: %s, dest: %s, size: %d, prio: %d)" % \
               (self.id, str(self.source), str(self.destination), self.__len__(), self.priority)


class HeaderException(Exception):
    pass


class MonitoredPackage(Package):
    def __init__(self, env, *args, **kwargs):
        super(MonitoredPackage, self).__init__(*args, **kwargs)
        self.env = env

    def on_hop(self, sender, receiver):
        pass

    def on_destination_reached(self, node):
        pass
