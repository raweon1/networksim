import simpy
import numpy as np
from collections import defaultdict, deque
from time import time


def sim_print(env, msg):
    if env.verbose:
        print("%0.2f:" % env.now + " " + msg)


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
    def __init__(self, source, destination, payload, priority=20, header=(0, "")):
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
        # todo check header
        self.headers.append(header)
        return self

    def __len__(self):
        t_len = self.payload
        for header in self.headers:
            t_len += header[0]
        return t_len

    def __str__(self):
        return "Package: (source: %s, dest: %s, size: %d, prio: %d)" % \
               (str(self.source), str(self.destination), self.__len__(), self.priority)


class Node(object):
    def __init__(self, env, address):
        self.env = env
        self.address = address
        self.interfaces = []

    def on_package_received(self, package, interface):
        sim_print(self.env, "%s: %s received on interface %s" % (str(self.address), str(package), str(interface)))

    def on_package_sending(self, package, interface):
        sim_print(self.env, "%s: %s sending on interface %s" % (str(self.address), str(package), str(interface)))

    def on_interface_added(self, interface):
        raise NotImplementedError("You have to implement this")

    # called by NetworkEnvironment when Node receives a package
    def push(self, package, interface):
        self.on_package_received(package, interface)

    # called when Node starts sending a package on interface x
    # returns timeout_event until package is completely send
    def pop(self, package, interface):
        send_event = self.env.send_package(package, self.address, interface)
        self.on_package_sending(package, interface)
        return send_event

    def add_interface(self, interface):
        self.interfaces.append(interface)
        self.on_interface_added(interface)

    def __str__(self):
        return str(self.address)


class NetworkBuilder(object):
    def __init__(self, channel_types):
        # channel_types = { type: physical_travel_factor }
        # physical_travel_factor in m/µs
        self.channel_types = channel_types
        # { address: Node }
        self._nodes = {}
        # {source: {interface_out: [destination, interface_in, bandwidth, physical_delay] }}
        self._table = defaultdict(dict)

    # time one bit takes to travel the physical layer
    def physical_delay(self, channel_type, channel_length):
        if channel_type is not None and self.channel_types is not None:
            return channel_length / self.channel_types[channel_type]
        return 0

    def append_nodes(self, *nodes):
        for node in nodes:
            self._nodes[node.address] = node
        return self

    # bandwidth in Mb/s, channel_length in m
    def connect_nodes(self, node_a, node_b, bandwidth=10, channel_type=None, channel_length=0):
        node_a_dict = self._table[node_a.address]
        node_b_dict = self._table[node_b.address]
        interface_a = node_a_dict.__len__() + 1
        interface_b = node_b_dict.__len__() + 1
        # Mb/s = 10^6b/s = 10^6b/10^6µs = x
        # b/µs = x
        # bandwidth doesn't need to be changed
        physical_delay = self.physical_delay(channel_type, channel_length)
        node_a_dict[interface_a] = [node_b.address, interface_b, bandwidth, physical_delay]
        node_b_dict[interface_b] = [node_a.address, interface_a, bandwidth, physical_delay]
        node_a.add_interface(interface_a)
        node_b.add_interface(interface_b)
        return self

    def get_nodes(self):
        return self._nodes

    def get_table(self):
        return self._table


class NetworkEnvironment(simpy.Environment):
    # Speed of light in m/µs : 299.792
    # {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792, "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
    # channel_types = { type: physical_travel_factor (in m/µs) }
    def __init__(self, channel_types=None, verbose=True, *args, **kwargs):
        super(NetworkEnvironment, self).__init__(*args, **kwargs)
        self.verbose = verbose
        self.builder = NetworkBuilder(channel_types)
        self._nodes = self.builder.get_nodes()
        self._table = self.builder.get_table()
        self.sleep_event = self.event()

    def send_package(self, package, source_address, interface_out):
        # receiver = [address, interface_in, bandwidth, physical_delay]
        receiver = self._table[source_address][interface_out]
        # package.__len__() in Bytes | receiver[2] = bandwidth in b/µs | receiver[3] physical delay in µs
        sending_time = ((package.__len__() * 8) / receiver[2]) + receiver[3]
        return self.process(self.send_package_process(package, self._nodes[receiver[0]], receiver[1], sending_time,
                                                      self._nodes[source_address]))
        # return self.process(
        #    SendPackageProcess(self, package, self._nodes[receiver[0]], receiver[1], sending_time).send_package())

    def send_package_process(self, package, receiver, interface_in, sending_time, sender):
        start_time = self.now
        sending = True
        while sending_time > 0:
            try:
                if sending:
                    yield self.timeout(sending_time)
                    sending_time = 0
                    receiver.push(package, interface_in)
                    package.on_hop(sender, receiver)
                    if receiver.address == package.destination:
                        package.on_destination_reached(receiver)
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                if sending:
                    sending_time -= self.now - start_time
                    # todo maybe sending_time += penalty (e.g. more bytes to transmit)
                else:
                    start_time = self.now
                sending = not sending


class Flow(Node):
    def __init__(self, env, address, destination):
        super(Flow, self).__init__(env, address)
        self.destination = destination
        self.processes = []

    def on_interface_added(self, interface):
        self.processes.append(self.env.process(self.run(interface)))

    def run(self, interface):
        while True:
            # package = payload, header, source, destination
            payload = np.random.randint(1, 5000)
            priority = np.random.randint(0, 3)
            package = Package(self.address, self.destination, payload, priority)
            # self.env.send_package(package, self.address, self.interface)
            yield self.pop(package, interface)
            sim_print(self.env, "%s: %s send on interface %s" % (str(self.address), str(package), str(interface)))
            # sleep_time = np.random.randint(4, 14)
            # yield self.env.timeout(sleep_time)


class Sink(Node):
    def __init__(self, env, address):
        super(Sink, self).__init__(env, address)

    def on_interface_added(self, interface):
        pass


class SinglePacket(Node):
    def __init__(self, env, address, destination, payload, wait_until, priority=20):
        super(SinglePacket, self).__init__(env, address)
        self.destination = destination
        self.payload = payload
        self.priority = priority
        self.wait_until = wait_until
        self.process = env.process(self.run())

    def on_interface_added(self, interface):
        pass

    def run(self):
        yield self.env.timeout(self.wait_until)
        package = Package(self.address, self.destination, self.payload, self.priority)
        yield self.pop(package, self.interfaces[0])


class SwitchBuffer(object):
    def next_package(self):
        raise NotImplementedError("You have to implement this")

    def append_package(self, package):
        raise NotImplementedError("You have to implement this")

    def remove(self, package):
        raise NotImplementedError("You have to implement this")

    def empty(self):
        raise NotImplementedError("You have to implement this")

    def __len__(self):
        raise NotImplementedError("You have to implement this")


class FCFS_Buffer(SwitchBuffer):
    def __init__(self):
        self.queue = deque([])

    def next_package(self):
        return self.queue[0]

    def append_package(self, package):
        self.queue.append(package)

    def remove(self, package):
        self.queue.popleft()

    def empty(self):
        return self.queue.__len__() == 0

    def __len__(self):
        return self.queue.__len__()


class LCFS_Buffer(SwitchBuffer):
    def __init__(self):
        self.queue = []

    def next_package(self):
        return self.queue[self.queue.__len__() - 1]

    def append_package(self, package):
        self.queue.append(package)

    def remove(self, package):
        self.queue.pop()

    def empty(self):
        return self.queue.__len__() == 0

    def __len__(self):
        return self.queue.__len__()


class Switch(Node):
    def __init__(self, env, address, buffer_type=FCFS_Buffer, aging_time=1000, preemption=False):
        super(Switch, self).__init__(env, address)
        # must be a subclass of SwitchBuffer - important: cannot be an instance of SwitchBuffer!
        self.buffer_type = buffer_type
        # time until entries in switch_table become invalid
        self.aging_time = aging_time
        # activate preemption for this Switch
        self.preemption = preemption
        # { source: interface_in, time }
        self.switch_table = {}
        # {interface: [buffer, process] }
        # buffer and simpy.process for each interface
        self.interface_modules = {}
        # sleeping event if buffer is empty
        self.sleep_event = env.event()

    def on_package_received(self, package, interface):
        sim_print(self.env, "%s: %s received on interface %s" % (str(self.address), str(package), str(interface)))
        # create entry in switch_table
        self.switch_table[package.source] = [interface, self.env.now]
        # valid switch_table entry -> add package to buffer of interface x
        # invalid switch_table entry -> broadcast package
        try:
            destination_entry = self.switch_table[package.destination]
            if self.env.now > destination_entry[1] + self.aging_time:
                self.broadcast_package(package, interface)
            else:
                self.interface_modules[interface][0].append_package(package)
                self.interface_modules[interface][1].interrupt("new package")
        except KeyError:
            self.broadcast_package(package, interface)

    def broadcast_package(self, package, interface_in):
        for interface, interface_module in self.interface_modules.items():
            # do not broadcast to source interface
            if interface != interface_in:
                interface_module[0].append_package(package)
                interface_module[1].interrupt("new package")

    def on_interface_added(self, interface):
        switch_buffer = self.buffer_type()
        if self.preemption:
            self.interface_modules[interface] = [switch_buffer, self.env.process(
                self.preemption_run(interface, switch_buffer))]
        else:
            self.interface_modules[interface] = [switch_buffer, self.env.process(self.run(interface, switch_buffer))]

    def run(self, interface, buffer):
        package = None
        if buffer.empty():
            try:
                yield self.sleep_event
            except simpy.Interrupt:
                package = buffer.next_package()
                sending_event = self.pop(package, interface)
        else:
            package = buffer.next_package()
            sending_event = self.pop(package, interface)
        while True:
            try:
                if not buffer.empty() or not sending_event.processed:
                    if sending_event.processed:
                        package = buffer.next_package()
                        sending_event = self.pop(package, interface)
                    yield sending_event
                    sim_print(self.env, "%s: %s send on interface %s" %
                              (str(self.address), str(package), str(interface)))
                    buffer.remove(package)
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                pass

    def preemption_run(self, interface, buffer):
        pending_events = {}
        sending_package = None
        if buffer.empty():
            try:
                yield self.sleep_event
            except simpy.Interrupt:
                sending_package = buffer.next_package()
                sending_event = self.pop(sending_package, interface)
        else:
            sending_package = buffer.next_package()
            sending_event = self.pop(sending_package, interface)
        while True:
            try:
                if not buffer.empty() or not sending_event.processed:
                    if sending_event.processed:
                        sending_package = buffer.next_package()
                        try:
                            sending_event = pending_events[sending_package]
                            sending_event.interrupt("continue sending")
                            sim_print(self.env, "%s: %s continued on interface %s" %
                                      (str(self.address), str(sending_package), str(interface)))
                        except KeyError:
                            sending_event = self.pop(sending_package, interface)
                    yield sending_event
                    sim_print(self.env, "%s: %s send on interface %s" %
                              (str(self.address), str(sending_package), str(interface)))
                    pending_events.pop(sending_package, None)
                    buffer.remove(sending_package)
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                package = buffer.next_package()
                if package != sending_package and not sending_event.processed:
                    pending_events[sending_package] = sending_event
                    sending_event.interrupt("stop sending")
                    sim_print(self.env, "%s: %s stopped on interface %s" %
                              (str(self.address), str(sending_package), str(interface)))
                    sending_package = package
                    sending_event = self.pop(sending_package, interface)


tmp = time()
some_channel_types = {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792,
                      "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
env = NetworkEnvironment(channel_types=some_channel_types)
builder = env.builder
nodes = [SinglePacket(env, "SP-1", "Sink", 5000, 0), SinglePacket(env, "SP-2", "Sink", 5000, 250),
         Switch(env, "Switch", preemption=True, buffer_type=LCFS_Buffer), Sink(env, "Sink")]
builder.append_nodes(*nodes).connect_nodes(nodes[0], nodes[2]).\
    connect_nodes(nodes[1], nodes[2]).connect_nodes(nodes[2], nodes[3])
env.run(until=100000)
print(time() - tmp)
