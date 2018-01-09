import simpy
import numpy as np


def sim_print(env, str):
    print("%0.2f:" % env.now + " " + str)


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
            raise HeaderException("%s has no header" % str(self))
        return self.headers[self.headers.__len__() - 1]

    def pop_header(self):
        if self.headers.__len__() == 0:
            raise HeaderException("%s has no header" % str(self))
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
        return "Package: (source: %s, dest: %s, size: %d)" % (str(self.source), str(self.destination), self.__len__())


class Node(object):
    def __init__(self, env, address):
        self.env = env
        self.address = address

    def on_package_received(self, package, interface):
        raise NotImplementedError("You have to implement this")

    def on_package_send(self, package, interface):
        raise NotImplementedError("You have to implement this")

    def push(self, package, interface):
        self.on_package_received(package, interface)

    def pop(self, package, interface):
        send_event = self.env.send_package(package, self.address, interface)
        self.on_package_send(package, interface)
        return send_event


class NetworkEnvironment(simpy.Environment):
    def __init__(self, *args, **kwargs):
        super(NetworkEnvironment, self).__init__(*args, **kwargs)
        self.travel_time = 1
        """
        { address: Node }
        """
        self.nodes = {}
        """
        {
            source: 
            {
                interface_out: [destination, interface_in, channel_type]
                ...
            }
            ...
        }
        """
        self.table = {}
        """
        (destination, interface, package, arrival_time)
        """
        self.packages_to_push = []
        self.sleep_event = self.event()
        self.next_package = None
        self.next_package_event = None
        self.push_process = self.process(self.send_package_proc())

    def bandwidth(self, channel_type):
        return 100

    def send_package(self, package, source, interface):
        # receiver = [destination, interface_in, channel_type]
        receiver = self.table[source][interface]
        sending_time = package.__len__() / self.bandwidth(receiver[2])
        arrival_time = self.now + sending_time + self.travel_time
        self.packages_to_push.append((receiver[0], receiver[1], package, arrival_time))
        self.push_process.interrupt("new package")
        return self.timeout(sending_time)

    def send_package_proc(self):
        while True:
            try:
                if self.packages_to_push.__len__() > 0:
                    if not self.next_package_event.processed:
                        yield self.next_package_event
                        self.nodes[self.next_package[0]].push(self.next_package[2], self.next_package[1])
                        self.packages_to_push.pop()
                    else:
                        self.packages_to_push.sort(reverse=True, key=lambda r: r[3])
                        self.next_package = self.packages_to_push[self.packages_to_push.__len__() - 1]
                        self.next_package_event = self.timeout(self.next_package[3] - self.now)
                        yield self.next_package_event
                        self.nodes[self.next_package[0]].push(self.next_package[2], self.next_package[1])
                        self.packages_to_push.pop()
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                self.packages_to_push.sort(reverse=True, key=lambda r: r[3])
                if self.next_package_event is None or self.next_package[3] > \
                        self.packages_to_push[self.packages_to_push.__len__() - 1][3]:
                    self.next_package = self.packages_to_push[0]
                    self.next_package_event = self.timeout(self.next_package[3] - self.now)


class Flow(Node):
    def __init__(self, env, address, interface, destinations):
        super(Flow, self).__init__(env, address)
        self.interface = interface
        self.destinations = destinations
        self.proc = env.process(self.run())

    def on_package_received(self, package, interface):
        pass

    def on_package_send(self, package, interface):
        sim_print(self.env, "%d: %s sending on interface %s" % (self.address, str(package), str(interface)))

    def run(self):
        while True:
            # payload, header, source, destination
            payload = np.random.randint(1, 5000)
            header = (np.random.randint(1, 15), "")
            destination = self.destinations[np.random.randint(0, self.destinations.__len__())]
            package = Package(payload, header, self.address, destination)
            # self.env.send_package(package, self.address, self.interface)
            yield self.pop(package, self.interface)
            sim_print(self.env, "%d: %s send on interface %s" % (self.address, str(package), str(self.interface)))
            # sleep_time = np.random.randint(4, 14)
            # yield self.env.timeout(sleep_time)


class Sink(Node):
    def __init__(self, env, address, interface):
        super(Sink, self).__init__(env, address)
        self.interface = interface

    def on_package_received(self, package, interface):
        sim_print(self.env, "%d: %s received on interface %s" % (self.address, str(package), str(interface)))

    def on_package_send(self, package, interface):
        pass


class Switch(Node):
    pass


class Builder(object):
    # todo
    pass


env = NetworkEnvironment()
nodes = {1337: Flow(env, 1337, "x", [17]), 17: Sink(env, 17, "y")}
table = {1337: {"x": [17, "y", 0]}}
env.nodes = nodes
env.table = table
env.run(until=1500)
