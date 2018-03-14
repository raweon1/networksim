import numpy as np
from math import sqrt
from collections import deque
from simpy import Interrupt

from simulation.frame import Frame


class Node(object):
    def __init__(self, env, address, monitor: bool = False):
        """
        :param env: NetworkEnvironment for this Frame
        :param address: Address of this node, should be unique and a string/int
        :param monitor: bool if you want to monitor this node
        """
        self.env = env
        self.address = address
        self.monitor = monitor
        self.ports = []

    def on_frame_received(self, frame: Frame, port_in: int):
        """
        called when a frame is received
        :param frame: received frame
        :param port_in: ingress port
        """
        self.env.sim_print("%s: %s received on port %s" % (str(self.address), str(frame), str(port_in)))

    def on_frame_sending(self, frame: Frame, port_out: int):
        """
        called when a node starts sending
        :param frame: frame to send
        :param port_out: egress port
        """
        self.env.sim_print("%s: %s sending on port %s" % (str(self.address), str(frame), str(port_out)))

    def on_port_added(self, port: int, bandwidth: float, *args):
        """
        called when a port is added to this node. most likely upon using NetworkBuilder.connect_node
        :param port: added port
        :param bandwidth: connection bandwidth
        :param args: further arguments if needed. Right now only switches need this parameter
        """
        pass

    def get_monitor_table(self):
        pass

    def get_monitor_results(self):
        pass

    # called by NetworkEnvironment when Node receives a frame
    def push(self, frame: Frame, port_in: int):
        """
        called by NetworkEnvironment when a Node receives a frame
        :param frame: frame to push to the receiving node
        :param port_in: ingress port of the receiving node
        """
        self.on_frame_received(frame, port_in)

    # called when Node starts sending a frame on port x
    # returns timeout_event until frame is completely send [AND an inspector for that event if inspector=True]
    def pop(self, frame: Frame, port_out: int, extra_bytes: int = 0, inspector: bool = False):
        """
        called when Node starts sending a frame on port x
        :param frame: frame to send
        :param port_out: egress port
        :param extra_bytes: additional bytes to send, this is to increase the sending time without altering the frame
        :param inspector: true if you want an inspector for the sending event, false otherwise
        :return: returns a sending_event until the frame is completely send [AND an inspector for that event if inspector=True]
        """
        send_event = self.env.send_frame(frame, self.address, port_out, extra_bytes, inspector)
        self.on_frame_sending(frame, port_out)
        return send_event

    def add_port(self, port, bandwidth, *args):
        self.ports.append(port)
        self.on_port_added(port, bandwidth, *args)

    def __str__(self):
        return str(self.address)


class Tmp(Node):
    def __init__(self, env, address, frame_generator, sleep_generator, monitor: bool = False):
        """
        :param env:
        :param address:
        :param frame_generator: generator which produces frames to send
        :param sleep_generator: generator which produces floats >= 0. This is the time in µs this process waits
        until a new frame is being send
        :param monitor:
        """
        super(Tmp, self).__init__(env, address, monitor)
        self.frame_queue = deque()
        self.sleep_event = self.env.event()
        self.sleeping = False
        self.frame_process = self.env.process(self.generate_frame(frame_generator, sleep_generator))
        self.send_process = self.env.process(self.send_frame())

    def generate_frame(self, frame_generator, sleep_generator):
        while True:
            frame = frame_generator.__next__()
            self.frame_queue.append(frame)
            if self.sleeping:
                self.send_process.interrupt("new frame")
            sleep_time = sleep_generator.__next__()
            yield self.env.timeout(sleep_time)

    def send_frame(self):
        # frage: bei monitored frames wird die zeit der erstellung genommen, ist das hier so gedacht?
        while True:
            try:
                if self.frame_queue.__len__() > 0:
                    self.env.sim_print("sending")
                    self.env.sim_print(self.frame_queue.__len__())
                    self.sleeping = False
                    frame = self.frame_queue.popleft()
                    yield self.pop(frame, self.ports[0])
                else:
                    self.env.sim_print("sleeping")
                    self.sleeping = True
                    yield self.sleep_event
            except Interrupt:
                pass


class Flow(Node):
    def __init__(self, env, address, destination_address):
        super(Flow, self).__init__(env, address)
        self.destination = destination_address
        self.processes = []

    def on_port_added(self, port, bandwidth, *args):
        self.processes.append(self.env.process(self.run(port)))

    def run(self, port):
        while True:
            # frame = source, destination, payload, priority=, header=
            payload = abs(np.random.normal(750, 700))
            priority = np.random.randint(0, 3)
            frame = Frame(self.env, self.address, self.destination, payload, priority)
            # self.env.send_frame(frame, self.address, self.port)
            yield self.pop(frame, port)
            self.env.sim_print("%s: %s send on port %s" % (str(self.address), str(frame), str(port)))
            # sleep_time = np.random.exponential(1.1)
            # yield self.env.timeout(sleep_time)


class Sink(Node):
    def __init__(self, env, address):
        super(Sink, self).__init__(env, address)


class SinglePacket(Node):
    def __init__(self, env, address, destination_address, payload, wait_until, priority=7):
        super(SinglePacket, self).__init__(env, address)
        self.destination = destination_address
        self.payload = payload
        self.priority = priority
        self.wait_until = wait_until
        self.process = env.process(self.run())

    def run(self):
        yield self.env.timeout(self.wait_until)
        frame = Frame(self.env, self.address, self.destination, self.payload, self.priority)
        yield self.pop(frame, self.ports[0])


class Flow2(Node):
    def __init__(self, env, address, frame_generator, monitor=False):
        super(Flow2, self).__init__(env, address, monitor)
        self.frame_generator = frame_generator
        self.frames = []
        self.process = env.process(self.run())

    def get_monitor_table(self):
        result = []
        for frame in self.frames:
            result += frame.get_hop_table()
        return result

    def get_monitor_results(self):
        self.frames.sort(reverse=True, key=lambda p: p.latency)
        _destination_reached_count = destination_reached_count(self.frames)
        if _destination_reached_count == 0:
            _average_frame_latency = -1
            _standard_deviation_latency = -1
        else:
            _average_frame_latency = average_frame_latency(self.frames, _destination_reached_count)
            _standard_deviation_latency = standard_deviation_latency(self.frames, _average_frame_latency,
                                                                     _destination_reached_count)
        _average_packet_size = average_packet_size(self.frames)
        _standard_deviation_packet_size = standard_deviation_packet_size(self.frames, _average_packet_size)
        results = {"frames_injected": self.frames.__len__(),
                   "frames_destination_reached": _destination_reached_count,
                   "average_packet_size": _average_packet_size,
                   "standard_deviation_packet_size": _standard_deviation_packet_size,
                   "average_frame_latency": _average_frame_latency,
                   "standard_deviation_frame_latency": _standard_deviation_latency}
        return results

    def run(self):
        while True:
            try:
                frame = self.frame_generator.__next__()
            except StopIteration:
                self.env.stop()
                break
            if self.monitor:
                self.frames.append(frame)
            yield self.pop(frame, self.ports[0])


class FrameInjector(Node):
    def __init__(self, env, address, injection_target_address, bandwidth,
                 intensity_generator, frame_generator, monitor=False):
        super(FrameInjector, self).__init__(env, address, monitor)
        self.injection_target_address = injection_target_address
        self.bandwidth = bandwidth
        self.intensity_generator = intensity_generator
        self.frame_generator = frame_generator
        self.frames = []
        self.process = env.process(self.run())

    def get_monitor_table(self):
        result = []
        for frame in self.frames:
            result += frame.get_hop_table()
        return result

    def get_monitor_results(self):
        self.frames.sort(reverse=True, key=lambda p: p.latency)
        _destination_reached_count = destination_reached_count(self.frames)
        if _destination_reached_count == 0:
            _average_frame_latency = -1
            _standard_deviation_latency = -1
        else:
            _average_frame_latency = average_frame_latency(self.frames, _destination_reached_count)
            _standard_deviation_latency = standard_deviation_latency(self.frames, _average_frame_latency,
                                                                     _destination_reached_count)
        _average_packet_size = average_packet_size(self.frames)
        _standard_deviation_packet_size = standard_deviation_packet_size(self.frames, _average_packet_size)
        results = {"frames_injected": self.frames.__len__(),
                   "frames_destination_reached": _destination_reached_count,
                   "average_packet_size": _average_packet_size,
                   "standard_deviation_packet_size": _standard_deviation_packet_size,
                   "average_frame_latency": _average_frame_latency,
                   "standard_deviation_frame_latency": _standard_deviation_latency}
        return results

    def run(self):
        injection_node = self.env.nodes[self.injection_target_address]
        while True:
            try:
                frame = self.frame_generator.__next__()
            except StopIteration:
                self.env.stop()
                break
            if self.monitor:
                self.frames.append(frame)
            injection_node.push(frame, "injected")
            sleep_factor = self.intensity_generator.__next__()
            sending_time = frame.__len__() * 8 / self.bandwidth
            yield self.env.timeout(sleep_factor * sending_time)


def average_packet_size(frames):
    average_frame_length = 0
    frame_count = frames.__len__()
    for frame in frames:
        average_frame_length += frame.__len__() / frame_count
    return average_frame_length


def standard_deviation_packet_size(frames, _average_packet_size):
    sd_frame_length = 0
    frame_count = frames.__len__() - 1 if frames.__len__() > 1 else 1
    for frame in frames:
        sd_frame_length += pow(frame.__len__() - _average_packet_size, 2) / frame_count
    return sqrt(sd_frame_length)


def destination_reached_count(frames):
    count = 0
    for frame in frames:
        if frame.latency < 0:
            break
        count += 1
    return count


# frames: list of MonitoredFrame's
# must be sorted by latency in reversed order
def average_frame_latency(frames, frame_count):
    _average_frame_latency = 0
    for frame in frames:
        if frame.latency < 0:
            break
        _average_frame_latency += frame.latency / frame_count
    return _average_frame_latency


# frames: list of MonitoredFrame's
# must be sorted by latency in reversed order
def standard_deviation_latency(frames, _average_frame_latency, frame_count):
    frame_count -= 1 if frame_count > 1 else 0
    sd_frame_latency = 0
    for frame in frames:
        if frame.latency < 0:
            break
        sd_frame_latency += pow(frame.latency - _average_frame_latency, 2) / frame_count
    return sqrt(sd_frame_latency)


# data = list of monitored Frames
def parse_node(monitored_node):
    data = monitored_node.frames
    monitored_node_address = monitored_node.address
    _average_packet_size = average_packet_size(data)
    _standard_deviation_packet_size = standard_deviation_packet_size(data, _average_packet_size)
    data.sort(reverse=True, key=lambda p: p.latency)
    frame_count = destination_reached_count(data)
    _average_frame_latency = average_frame_latency(data, frame_count)
    _standard_deviation_latency = standard_deviation_latency(data, _average_frame_latency, frame_count)

    print()
    print(monitored_node_address)
    print("frames send:                           %s" % str(data.__len__()))
    print("frames destination reached:            %d" % frame_count)
    print("average frame size:                    %s Byte" % str(_average_packet_size))
    print("standard deviation frame size:         %s Byte" % str(_standard_deviation_packet_size))
    print("average latency in µs:                   %s" % str(_average_frame_latency))
    print("standard deviation latency :             %s" % str(_standard_deviation_latency))
