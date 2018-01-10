import simpy
import numpy as np
from collections import defaultdict, deque


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
        self.interfaces = []

    def on_package_received(self, package, interface):
        raise NotImplementedError("You have to implement this")

    def on_package_send(self, package, interface):
        raise NotImplementedError("You have to implement this")

    def on_interface_added(self, interface):
        raise NotImplementedError("You have to implement this")

    # called when Node receives a package
    def push(self, package, interface):
        self.on_package_received(package, interface)

    # called when Node starts sending a package on interface x
    # returns timeout_event until package is completely send
    def pop(self, package, interface):
        send_event = self.env.send_package(package, self.address, interface)
        self.on_package_send(package, interface)
        return send_event

    def add_interface(self, interface):
        self.interfaces.append(interface)
        self.on_interface_added(interface)


class NetworkBuilder(object):
    def __init__(self, channel_types):
        # channel_types = { type: physical_travel_factor }
        self.channel_types = channel_types
        # { address: Node }
        self._nodes = {}
        # {source: {interface_out: [destination, interface_in, bandwidth, physical_delay] }}
        self._table = defaultdict(dict)

    # time one bit takes to travel the physical layer
    def physical_delay(self, channel_type, channel_length):
        if channel_type is not None and self.channel_types is not None:
            return channel_length * self.channel_types[channel_type]
        return 0

    def append_nodes(self, *nodes):
        for node in nodes:
            self._nodes[node.address] = node
        return self

    # bandwidth in Mb/s
    def connect_nodes(self, node_a, node_b, bandwidth=10, channel_type=None, channel_length=0):
        node_a_dict = self._table[node_a.address]
        node_b_dict = self._table[node_b.address]
        interface_a = node_a_dict.__len__() + 1
        interface_b = node_b_dict.__len__() + 1
        # Mb/s = 10^6b/s = 10^6b/10^6µs = x
        # b/µs = x
        node_a_dict[interface_a] = [node_b.address, interface_b, bandwidth,
                                    self.physical_delay(channel_type, channel_length)]
        node_b_dict[interface_b] = [node_a.address, interface_a, bandwidth,
                                    self.physical_delay(channel_type, channel_length)]
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
    # channel_types = { type: physical_travel_factor }
    def __init__(self, channel_types=None, *args, **kwargs):
        super(NetworkEnvironment, self).__init__(*args, **kwargs)
        self.builder = NetworkBuilder(channel_types)
        self._nodes = self.builder.get_nodes()
        self._table = self.builder.get_table()
        # (destination, interface_in, package, arrival_time)
        self.packages_to_push = []
        self.sleep_event = self.event()
        self.push_process = self.process(self.send_package_proc())

    def send_package(self, package, source, interface):
        # receiver = [destination, interface_in, bandwidth, physical_delay]
        receiver = self._table[source][interface]
        # time it takes to put the packet on the channel
        # package.__len__() is Bytes | receiver[2] = bandwidth is b/µs
        sending_time = (package.__len__() * 8) / receiver[2]
        arrival_time = self.now + sending_time + receiver[3]
        self.packages_to_push.append((receiver[0], receiver[1], package, arrival_time))
        self.push_process.interrupt("new package")
        return self.timeout(sending_time)

    def send_package_proc(self):
        package = None
        package_event = None
        while True:
            try:
                if self.packages_to_push.__len__() > 0:
                    if not package_event.processed:
                        yield package_event
                        self._nodes[package[0]].push(package[2], package[1])
                        self.packages_to_push.pop()
                    else:
                        self.packages_to_push.sort(reverse=True, key=lambda r: r[3])
                        package = self.packages_to_push[self.packages_to_push.__len__() - 1]
                        package_event = self.timeout(package[3] - self.now)
                        yield package_event
                        self._nodes[package[0]].push(package[2], package[1])
                        self.packages_to_push.pop()
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                self.packages_to_push.sort(reverse=True, key=lambda r: r[3])
                if package_event is None or package[3] > \
                        self.packages_to_push[self.packages_to_push.__len__() - 1][3]:
                    package = self.packages_to_push[self.packages_to_push.__len__() - 1]
                    package_event = self.timeout(package[3] - self.now)


class Flow(Node):
    def __init__(self, env, address, destination):
        super(Flow, self).__init__(env, address)
        self.destination = destination
        self.procs = []

    def on_package_received(self, package, interface):
        sim_print(self.env, "%s: %s received on interface %s" % (str(self.address), str(package), str(interface)))

    def on_package_send(self, package, interface):
        sim_print(self.env, "%s: %s sending on interface %s" % (str(self.address), str(package), str(interface)))

    def on_interface_added(self, interface):
        self.procs.append(self.env.process(self.run(interface)))

    def run(self, interface):
        while True:
            # package = payload, header, source, destination
            payload = np.random.randint(1, 5000)
            header = (np.random.randint(1, 15), "")
            package = Package(payload, header, self.address, self.destination)
            # self.env.send_package(package, self.address, self.interface)
            yield self.pop(package, interface)
            sim_print(self.env, "%s: %s send on interface %s" % (str(self.address), str(package), str(interface)))
            # sleep_time = np.random.randint(4, 14)
            # yield self.env.timeout(sleep_time)


class Sink(Node):
    def __init__(self, env, address):
        super(Sink, self).__init__(env, address)

    def on_package_received(self, package, interface):
        sim_print(self.env, "%s: %s received on interface %s" % (str(self.address), str(package), str(interface)))

    def on_package_send(self, package, interface):
        pass

    def on_interface_added(self, interface):
        pass


class SwitchBuffer(object):
    def next_package(self):
        raise NotImplementedError("You have to implement this")

    def empty(self):
        raise NotImplementedError("You have to implement this")

    def append_package(self, package):
        raise NotImplementedError("You have to implement this")

    def __len__(self):
        raise NotImplementedError("You have to implement this")


class FCFS_Scheduler(SwitchBuffer):
    def __init__(self):
        self.queue = deque([])

    def append_package(self, package):
        self.queue.append(package)

    def empty(self):
        return self.queue.__len__() == 0

    def next_package(self):
        return self.queue.popleft()

    def __len__(self):
        return self.queue.__len__()


class Switch(Node):
    def __init__(self, env, address, buffer_type=FCFS_Scheduler, aging_time=1000, preemption=False):
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

    def broadcast_package(self, package, source):
        for interface, interface_module in self.interface_modules.items():
            # do not broadcast to source interface
            if interface != source:
                interface_module[0].append_package(package)
                interface_module[1].interrupt("new package")

    def on_package_send(self, package, interface):
        sim_print(self.env, "%s: %s sending on interface %s" % (str(self.address), str(package), str(interface)))

    def on_interface_added(self, interface):
        switch_buffer = self.buffer_type()
        self.interface_modules[interface] = [switch_buffer, self.env.process(self.run(interface, switch_buffer))]

    def run(self, interface, buffer):
        delay = None
        while True:
            try:
                if not buffer.empty():
                    if delay.processed:
                        package = buffer.next_package()
                        delay = self.pop(package, interface)
                    yield delay
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                if delay is None:
                    package = buffer.next_package()
                    delay = self.pop(package, interface)


some_channel_types = {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792,
                      "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
env = NetworkEnvironment(channel_types=some_channel_types)
builder = env.builder
nodes = [Flow(env, "Flow-1", "Flow-2"), Switch(env, "Switch-1"), Flow(env, "Flow-2", "Flow-1"), Sink(env, "Sink-1")]
builder.append_nodes(*nodes).connect_nodes(nodes[0], nodes[1]).connect_nodes(nodes[1], nodes[2]).\
    connect_nodes(nodes[1], nodes[3])
env.run(until=10500)
print("Simulation-time in µs")
