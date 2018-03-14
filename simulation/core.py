import simpy
from collections import defaultdict
import numpy as np

from simulation.switch import Switch, SwitchPortParam
from simulation.frame import Frame
from simulation.node import Node


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


class NetworkEnvironment(simpy.Environment):
    # Speed of light in m/µs : 299.792
    # {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792, "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
    # channel_types = { type: physical_travel_factor (in m/µs) }

    id = {}

    def __init__(self, name="no_name", seed: int = None, channel_types: dict = None, verbose: bool = True,
                 min_preemption_bytes: int = 80, preemption_penalty_bytes: int = 8, *args, **kwargs):
        """
        :param name: Name of this Simulation
        :param seed: Seed of this Simulations random generator
        :param channel_types: available types of connections between nodes for this simulation. Form must be:
        channel_types = { type: physical_travel_factor (in m/µs), ...}
        :param verbose: bool for printing events
        :param min_preemption_bytes: int, minimum amount of bytes left to send before interrupting sending_event
        for frame preemption
        :param preemption_penalty_bytes: int, amount of extra bytes to send for interrupting a sending_event
        """
        super(NetworkEnvironment, self).__init__(*args, **kwargs)
        self.name = name
        try:
            self.id = NetworkEnvironment.id[name]
            NetworkEnvironment.id[name] += 1
        except KeyError:
            self.id = 1
            NetworkEnvironment.id[name] = 2
        self.next_frame_id = 0
        self.random = np.random.RandomState(seed=seed)
        self.seed = seed if seed is not None else ""
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

    def get_monitor_tables(self):
        """
        :return: dict of lists of monitored information
        """
        result = defaultdict(list)
        for node in self.nodes.values():
            if node.monitor:
                # list of dicts
                node_monitor_table = node.get_monitor_table()
                if node_monitor_table.__len__() > 0:
                    # combine tables with equal columns
                    index = "".join(key for key in node_monitor_table[0].keys())
                    result[index] += node_monitor_table
        return result

    def get_monitor_results(self):
        result = {}
        for node in self.nodes.values():
            if node.monitor:
                result[node.address] = node.get_monitor_results()
        return result

    def get_frame_id(self):
        self.next_frame_id += 1
        return self.next_frame_id - 1

    # returns a process to yield and an inspector
    def send_frame(self, frame: Frame, source_address, port_out: int, extra_bytes: int = 0, inspector: bool = False):
        # receiver = [address, port_in, bandwidth, physical_delay]
        """
        :param frame: frame to send
        :param source_address: address of the sending node
        :param port_out: egress port of the sending node
        :param extra_bytes: additional bytes to transmit
        :param inspector: bool if you want an inspector
        :return: returns a sending_event process to yield and an inspector
        """
        receiver = self.table[source_address][port_out]
        # frame.__len__() in Bytes | receiver[2] = bandwidth in b/µs | receiver[3] physical delay in µs
        sending_time = (((frame.__len__() + extra_bytes) * 8) / receiver[2]) + receiver[3]
        # inspector contains finish_time, the sim_time when the frame is send. this is important for preemption
        if inspector:
            inspector = SendingProcessInspector(self, receiver[2], self.min_preemption_bytes,
                                                self.preemption_penalty_bytes)
            return self.process(self.send_frame_process(frame, self.nodes[receiver[0]], receiver[1], sending_time,
                                                        self.nodes[source_address], inspector)), inspector
        else:
            return self.process(self.send_frame_process(frame, self.nodes[receiver[0]], receiver[1], sending_time,
                                                        self.nodes[source_address]))

    # do not interrupt this process without an inspector and checking finish_time
    # (this can cause a bug when you interrupt this process at the same time as it would be processed)
    # for this reason a runtime error (inspector is none) will occur to prevent interrupting without an inspector
    def send_frame_process(self, frame: Frame, receiver: Node, port_in: int, sending_time: float, sender: Node,
                           inspector: SendingProcessInspector = None):
        """
        :param frame: frame that is being send
        :param receiver: receiving node
        :param port_in: receiving node ingress port
        :param sending_time: time it takes to send this frame
        :param sender: sending node
        :param inspector: inspector
        """
        start_time = self.now
        if inspector is not None:
            inspector.finish_time = self.now + sending_time
        sending = True
        while sending_time > 0:
            try:
                if sending:
                    yield self.timeout(sending_time)
                    sending_time = 0
                    receiver.push(frame, port_in)
                    frame.on_hop(sender, receiver)
                    if receiver.address == frame.destination:
                        frame.on_destination_reached(receiver)
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                if sending:
                    sending_time -= self.now - start_time
                    inspector.finish_time = -1
                else:
                    start_time = self.now
                    # some bytes need to be transmitted to signal that the frame is continued
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
        # {source: {port_out: [destination, port_in, bandwidth, physical_delay] }}
        self.table = defaultdict(dict)
        # {source: {destination: [destination, port_in, bandwidth, physical_delay] }}
        self.table2 = defaultdict(list)

    # time one bit takes to travel the physical layer
    def physical_delay(self, channel_type, channel_length):
        """
        :param channel_type: channel_type defined for this simulation in the NetworkEnvironment
        :param channel_length: Meter
        :return: time one bit takes to travel the physical layer
        """
        if channel_type is not None and self.channel_types is not None:
            return channel_length / self.channel_types[channel_type]
        return 0

    def append_nodes(self, *nodes):
        """
        :param nodes: Node[s] to append
        :return: returns NetworkBuilder
        """
        for node in nodes:
            self.nodes[node.address] = node
        return self

    # bandwidth in Mb/s, channel_length in m
    def connect_nodes(self, node_a: Node, node_b: Node, bandwidth: int = 10, channel_type=None, channel_length: int = 0,
                      *switch_params: SwitchPortParam):
        """
        :param node_a: first Node to connect
        :param node_b: second Node to connect
        :param bandwidth: bandwidth of this connection
        :param channel_type: channel_type defined for this simulation in the NetworkEnvironment
        :param channel_length: in meter
        :param switch_params: up to two SwitchPortParam. The first SwitchPortParam is used for the first Switch
        :return: returns NetworkBuilder
        """
        node_a_dict = self.table[node_a.address]
        node_b_dict = self.table[node_b.address]
        port_a = node_a_dict.__len__() + 1
        port_b = node_b_dict.__len__() + 1
        # Mb/s = 10^6b/s = 10^6b/10^6µs = x
        # b/µs = x
        # bandwidth doesn't need to be changed
        physical_delay = self.physical_delay(channel_type, channel_length)
        node_a_dict[port_a] = [node_b.address, port_b, bandwidth, physical_delay]
        node_b_dict[port_b] = [node_a.address, port_a, bandwidth, physical_delay]

        if isinstance(node_a, Switch) and switch_params.__len__() > 0:
            node_a.add_port(port_a, bandwidth, switch_params[0])
            if isinstance(node_b, Switch) and switch_params.__len__() > 1:
                node_b.add_port(port_b, bandwidth, switch_params[1])
            else:
                node_b.add_port(port_b, bandwidth)
        else:
            node_a.add_port(port_a, bandwidth)
            if isinstance(node_b, Switch) and switch_params.__len__() > 0:
                node_b.add_port(port_b, bandwidth, switch_params[0])
            else:
                node_b.add_port(port_b, bandwidth)

        self.table2[(node_a.address, node_b.address)] = [bandwidth, physical_delay]
        self.table2[(node_b.address, node_a.address)] = [bandwidth, physical_delay]
        return self
