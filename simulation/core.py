import simpy
from collections import defaultdict


class NetworkEnvironment(simpy.Environment):
    # Speed of light in m/µs : 299.792
    # {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792, "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
    # channel_types = { type: physical_travel_factor (in m/µs) }
    def __init__(self, channel_types=None, verbose=True, min_preemption_bytes=80, preemption_penalty_bytes=8, *args,
                 **kwargs):
        super(NetworkEnvironment, self).__init__(*args, **kwargs)
        self.verbose = verbose
        self.min_preemption_bytes = min_preemption_bytes if min_preemption_bytes > 0 else 1
        self.preemption_penalty_bytes = preemption_penalty_bytes
        self.builder = NetworkBuilder(channel_types)
        self.nodes = self.builder.nodes
        self.table = self.builder.table
        self.stop_event = self.event()
        self.sleep_event = self.event()

    def sim_print(self, msg):
        if self.verbose:
            print("%0.2f: %s" % (self.now, msg))

    # if until <= 0: run until stop() has been called
    def run(self, until=None):
        if isinstance(until, int) and until <= 0:
            super(NetworkEnvironment, self).run(until=self.stop_event)
        else:
            super(NetworkEnvironment, self).run(until)

    def stop(self):
        self.stop_event.succeed()

    def get_monitor_results(self):
        result = {}
        for node in self.nodes.values():
            if node.monitor:
                result[node.address] = node.get_monitor_results()
        return result

    # returns a process to yield and an inspector
    def send_package(self, package, source_address, interface_out, extra_bytes=0, inspector=False):
        # receiver = [address, interface_in, bandwidth, physical_delay]
        receiver = self.table[source_address][interface_out]
        # package.__len__() in Bytes | receiver[2] = bandwidth in b/µs | receiver[3] physical delay in µs
        sending_time = (((package.__len__() + extra_bytes) * 8) / receiver[2]) + receiver[3]
        # inspector contains finish_time, the sim_time when the package is send. this is important for preemption
        if inspector:
            inspector = SendingProcessInspector(self, receiver[2], self.min_preemption_bytes,
                                                self.preemption_penalty_bytes)
            return self.process(self.send_package_process(package, self.nodes[receiver[0]], receiver[1], sending_time,
                                                          self.nodes[source_address], inspector)), inspector
        else:
            return self.process(self.send_package_process(package, self.nodes[receiver[0]], receiver[1], sending_time,
                                                          self.nodes[source_address]))

    # do not interrupt this process without an inspector and checking finish_time
    # (this can cause a bug when you interrupt this process at the same time as it would be processed)
    # for this reason a runtime error (inspector is none) will occur to prevent interrupting without an inspector
    def send_package_process(self, package, receiver, interface_in, sending_time, sender, inspector=None):
        start_time = self.now
        if inspector is not None:
            inspector.finish_time = self.now + sending_time
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
                    inspector.finish_time = -1
                else:
                    start_time = self.now
                    # some bytes need to be transmitted to signal that the package is continued
                    sending_time += inspector.get_penalty_time()
                    inspector.finish_time = self.now + sending_time
                sending = not sending


class NetworkBuilder(object):
    def __init__(self, channel_types):
        # channel_types = { type: physical_travel_factor }
        # physical_travel_factor in m/µs
        self.channel_types = channel_types
        # { address: Node }
        self.nodes = {}
        # {source: {interface_out: [destination, interface_in, bandwidth, physical_delay] }}
        self.table = defaultdict(dict)

    # time one bit takes to travel the physical layer
    def physical_delay(self, channel_type, channel_length):
        if channel_type is not None and self.channel_types is not None:
            return channel_length / self.channel_types[channel_type]
        return 0

    def append_nodes(self, *nodes):
        for node in nodes:
            self.nodes[node.address] = node
        return self

    # bandwidth in Mb/s, channel_length in m
    def connect_nodes(self, node_a, node_b, bandwidth=10, channel_type=None, channel_length=0):
        node_a_dict = self.table[node_a.address]
        node_b_dict = self.table[node_b.address]
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


class SendingProcessInspector(object):
    def __init__(self, env, bandwidth, min_preemption_bytes=80, penalty_bytes=8):
        self.env = env
        self.bandwidth = bandwidth
        self.min_preemption_bytes = min_preemption_bytes
        self.penalty_time = penalty_bytes * 8 / bandwidth
        self.penalty_bytes = penalty_bytes
        self.finish_time = 0

    def process_interruptable(self):
        bytes_left = (self.finish_time - self.env.now) * self.bandwidth / 8
        if self.finish_time < 0 or bytes_left - self.penalty_bytes > self.min_preemption_bytes:
            return True
        else:
            return False

    def get_penalty_time(self):
        return self.penalty_time
