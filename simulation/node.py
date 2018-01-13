import numpy as np
from math import sqrt

from simulation.package import *


class Node(object):
    def __init__(self, env, address, monitor=False):
        self.env = env
        self.address = address
        self.monitor = monitor
        self.interfaces = []

    def on_package_received(self, package, interface_in):
        self.env.sim_print("%s: %s received on interface %s" % (str(self.address), str(package), str(interface_in)))

    def on_package_sending(self, package, interface_out):
        self.env.sim_print("%s: %s sending on interface %s" % (str(self.address), str(package), str(interface_out)))

    def on_interface_added(self, interface):
        pass

    def get_monitor_results(self):
        pass

    # called by NetworkEnvironment when Node receives a package
    def push(self, package, interface_in):
        self.on_package_received(package, interface_in)

    # called when Node starts sending a package on interface x
    # returns timeout_event until package is completely send [AND an inspector for that event if inspector=True]
    def pop(self, package, interface_out, extra_bytes=0, inspector=False):
        send_event = self.env.send_package(package, self.address, interface_out, extra_bytes, inspector)
        self.on_package_sending(package, interface_out)
        return send_event

    def add_interface(self, interface):
        self.interfaces.append(interface)
        self.on_interface_added(interface)

    def __str__(self):
        return str(self.address)


class Flow(Node):
    def __init__(self, env, address, destination_address):
        super(Flow, self).__init__(env, address)
        self.destination = destination_address
        self.processes = []

    def on_interface_added(self, interface):
        self.processes.append(self.env.process(self.run(interface)))

    def run(self, interface):
        while True:
            # package = source, destination, payload, priority=, header=
            payload = abs(np.random.normal(750, 700))
            priority = np.random.randint(0, 3)
            package = Package(self.address, self.destination, payload, priority)
            # self.env.send_package(package, self.address, self.interface)
            yield self.pop(package, interface)
            self.env.sim_print("%s: %s send on interface %s" % (str(self.address), str(package), str(interface)))
            # sleep_time = np.random.exponential(1.1)
            # yield self.env.timeout(sleep_time)


class Sink(Node):
    def __init__(self, env, address):
        super(Sink, self).__init__(env, address)

    def on_interface_added(self, interface):
        pass


class SinglePacket(Node):
    def __init__(self, env, address, destination_address, payload, wait_until, priority=20):
        super(SinglePacket, self).__init__(env, address)
        self.destination = destination_address
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


class PackageInjector(Node):
    def __init__(self, env, address, injection_target_address, bandwidth,
                 intensity_generator, package_generator, monitor=False):
        super(PackageInjector, self).__init__(env, address, monitor)
        self.injection_target_address = injection_target_address
        self.bandwidth = bandwidth
        self.intensity_generator = intensity_generator
        self.package_generator = package_generator
        self.packages = []
        self.process = env.process(self.run())

    def get_monitor_results(self):
        self.packages.sort(reverse=True, key=lambda p: p.latency)
        _destination_reached_count = destination_reached_count(self.packages)
        _average_packet_size = average_packet_size(self.packages)
        _standard_deviation_packet_size = standard_deviation_packet_size(self.packages, _average_packet_size)
        _average_package_latency = average_package_latency(self.packages, _destination_reached_count)
        _standard_deviation_latency = standard_deviation_latency(self.packages, _average_package_latency,
                                                                 _destination_reached_count)
        results = {"average_packet_size": _average_packet_size,
                   "standard_deviation_packet_size": _standard_deviation_packet_size,
                   "average_package_latency": _average_package_latency,
                   "standard_deviation_latency": _standard_deviation_latency}
        return results

    def run(self):
        injection_node = self.env.nodes[self.injection_target_address]
        while True:
            try:
                package = self.package_generator.__next__()
            except StopIteration:
                self.env.stop()
                break
            if self.monitor:
                self.packages.append(package)
            injection_node.push(package, "injected")
            sleep_factor = self.intensity_generator.__next__()
            sending_time = package.__len__() * 8 / self.bandwidth
            yield self.env.timeout(sleep_factor * sending_time)


def average_packet_size(packages):
    average_package_length = 0
    package_count = packages.__len__()
    for package in packages:
        average_package_length += package.__len__() / package_count
    return average_package_length


def standard_deviation_packet_size(packages, _average_packet_size):
    sd_package_length = 0
    package_count = packages.__len__() - 1
    for package in packages:
        sd_package_length += pow(package.__len__() - _average_packet_size, 2) / package_count
    return sqrt(sd_package_length)


def destination_reached_count(packages):
    count = 0
    for package in packages:
        if package.latency < 0:
            break
        count += 1
    return count


# packages: list of MonitoredPackage's
# must be sorted by latency in reversed order
def average_package_latency(packages, package_count):
    _average_package_latency = 0
    for package in packages:
        if package.latency < 0:
            break
        _average_package_latency += package.latency / package_count
    return _average_package_latency


# packages: list of MonitoredPackage's
# must be sorted by latency in reversed order
def standard_deviation_latency(packages, _average_package_latency, package_count):
    package_count -= 1
    sd_package_latency = 0
    for package in packages:
        if package.latency < 0:
            break
        sd_package_latency += pow(package.latency - _average_package_latency, 2) / package_count
    return sqrt(sd_package_latency)


# data = list of monitored Packages
def parse_node(monitored_node):
    data = monitored_node.packages
    monitored_node_address = monitored_node.address
    _average_packet_size = average_packet_size(data)
    _standard_deviation_packet_size = standard_deviation_packet_size(data, _average_packet_size)
    data.sort(reverse=True, key=lambda p: p.latency)
    package_count = destination_reached_count(data)
    _average_package_latency = average_package_latency(data, package_count)
    _standard_deviation_latency = standard_deviation_latency(data, _average_package_latency, package_count)

    print()
    print(monitored_node_address)
    print("packages send:                           %s" % str(data.__len__()))
    print("packages destination reached:            %d" % package_count)
    print("average package size:                    %s Byte" % str(_average_packet_size))
    print("standard deviation package size:         %s Byte" % str(_standard_deviation_packet_size))
    print("average latency in µs:                   %s" % str(_average_package_latency))
    print("standard deviation latency :             %s" % str(_standard_deviation_latency))
