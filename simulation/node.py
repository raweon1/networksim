import numpy as np

from simulation.package import *


class Node(object):
    def __init__(self, env, address):
        self.env = env
        self.address = address
        self.interfaces = []

    def on_package_received(self, package, interface_in):
        self.env.sim_print("%s: %s received on interface %s" % (str(self.address), str(package), str(interface_in)))

    def on_package_sending(self, package, interface_out):
        self.env.sim_print("%s: %s sending on interface %s" % (str(self.address), str(package), str(interface_out)))

    def on_interface_added(self, interface):
        raise NotImplementedError("You have to implement this")

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
    def __init__(self, env, address, destination):
        super(Flow, self).__init__(env, address)
        self.destination = destination
        self.processes = []

    def on_interface_added(self, interface):
        self.processes.append(self.env.process(self.run(interface)))

    def run(self, interface):
        while True:
            # package = payload, header, source, destination
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
