from collections import defaultdict, deque
from math import sqrt

from simulation.frame import Frame


class SwitchBuffer(object):
    def __init__(self, env, port_transmit_rate: int, traffic_class_map, tsa_map, config, monitor: bool = False):
        """
        :param env:
        :param port_transmit_rate: Bandwdith of the connection
        :param traffic_class_map: PriorityMap for this port
        :param tsa_map: TransmissionSelectionAlgorithmMap for this port
        :param config: TrafficClassBandwidthMap for this port
        :param monitor:
        """
        self.env = env
        self.monitor = monitor
        self.data = defaultdict(list)
        self.t_class_p_map = traffic_class_map
        self.config = config
        # tsa = transmission selection algorithm
        self.tsa = []
        for tsa, delta_bandwidth in zip(tsa_map.transmission_selection_algorithm_per_traffic_class,
                                        config.bandwidth_param):
            self.tsa.append(tsa(port_transmit_rate, delta_bandwidth))

    # returns the next frame for transmission
    # selects the frame from the highest traffic class which has a frame available
    # see 802.1Q page: 127, block: 8.6.8
    def peek_next_frame(self):
        for tsa in reversed(self.tsa):
            frame = tsa.get_frame(self.env.now)
            if frame is not None:
                return frame
        return None

    def append_frame(self, frame: Frame):
        if self.monitor:
            self.data["append"].append((self.env.now, self.__len__(), frame))
        self.tsa[self.t_class_p_map.get_traffic_class(frame.priority)].append_frame(self.env.now, frame)

    # drops a frame without transmitting it
    def drop_frame(self, frame: Frame):
        if self.monitor:
            self.data["drop"].append((self.env.now, self.__len__(), frame))
        self.tsa[self.t_class_p_map.get_traffic_class(frame.priority)].remove_frame(self.env.now, frame)

    # called when transmission of a frame is started
    def transmission_start(self, frame: Frame):
        """
        called when transmission of a frame is started
        :param frame:
        """
        self.tsa[self.t_class_p_map.get_traffic_class(frame.priority)].transmitting(self.env.now, True)

    # called when transmission of a frame is paused, e.g. frame preemption
    def transmission_pause(self, frame: Frame):
        """
        called when transmission of a frame is paused, e.g. frame preemption
        :param frame:
        """
        self.tsa[self.t_class_p_map.get_traffic_class(frame.priority)].transmitting(self.env.now, False)

    # called when transmission of a frame is done, the frame is removed from the queue
    def transmission_done(self, frame: Frame):
        """
        called when transmission of a frame is done, the frame is removed from the queue
        :param frame:
        """
        if self.monitor:
            self.data["pop"].append((self.env.now, self.__len__(), frame))
        traffic_class = self.t_class_p_map.get_traffic_class(frame.priority)
        self.tsa[traffic_class].remove_frame(self.env.now, frame)
        self.tsa[traffic_class].transmitting(self.env.now, False)

    def empty(self):
        return self.__len__() == 0

    def __len__(self):
        length = 0
        for tsa in self.tsa:
            length += tsa.queue.__len__()
        return length


class FrameQueue(object):
    def append(self, frame):
        pass

    def remove(self, frame):
        pass

    def get_head_frame(self):
        pass

    def __len__(self):
        pass


class FrameFIFO(FrameQueue):
    def __init__(self):
        self.queue = deque()

    def append(self, frame):
        self.queue.append(frame)

    def remove(self, frame):
        self.queue.remove(frame)

    def get_head_frame(self):
        return self.queue[0]

    def __len__(self):
        return self.queue.__len__()


class TransmissionSelectionAlgorithm(object):
    def __init__(self, port_transmit_rate: int, delta_bandwidth: float, queue: FrameQueue = None):
        """

        :param port_transmit_rate: Bandwdith of the connection
        :param delta_bandwidth: usage of the available bandwidth in %. 0-1
        :param queue: Queuetype for this TransmissionSelectionAlgorithm
        """
        self.port_transmit_rate = port_transmit_rate
        self.delta_bandwidth = delta_bandwidth
        self.queue = queue if queue is not None else FrameFIFO()

    # returns a frame if a frame is available for transmission, None otherwise
    def get_frame(self, time):
        return None

    # appends a frame to the queue
    def append_frame(self, time, frame):
        self.queue.append(frame)

    # removes a frame from the queue, e.g. frame has been transmitted or dropped
    def remove_frame(self, time, frame):
        self.queue.remove(frame)

    def transmitting(self, time, status):
        pass


class StrictPriorityAlgorithm(TransmissionSelectionAlgorithm):
    def __init__(self, *args, **kwargs):
        super(StrictPriorityAlgorithm, self).__init__(*args, **kwargs)

    def get_frame(self, time):
        if self.queue.__len__() > 0:
            return self.queue.get_head_frame()
        else:
            return None


# see 802.1Q, page: 128, block: 8.6.8.2
class CreditBasedShaper(TransmissionSelectionAlgorithm):
    def __init__(self, *args, **kwargs):
        super(CreditBasedShaper, self).__init__(*args, **kwargs)

        # in bit / µs
        self.idle_slope = self.delta_bandwidth * self.port_transmit_rate

        self.transmit = False
        self.transmit_allowed = True
        self.credit = 0
        self.send_slope = self.idle_slope - self.port_transmit_rate

        self.transmit_time = 0

    def append_frame(self, time, frame):
        self.update_credit(time)
        self.queue.append(frame)

    def get_frame(self, time):
        self.update_credit(time)
        if self.queue.__len__() > 0 and self.transmit_allowed:
            return self.queue.get_head_frame()
        return None

    def transmitting(self, time, status):
        self.update_credit(time)
        self.transmit = status

    def update_credit(self, time):
        passed_time = time - self.transmit_time
        if self.transmit:
            self.credit += passed_time * self.send_slope
        else:
            self.credit += passed_time * self.idle_slope

        if self.queue.__len__() == 0 and self.credit > 0 and not self.transmit:
            self.credit = 0

        if self.credit >= 0:
            self.transmit_allowed = True
        else:
            self.transmit_allowed = False
        self.transmit_time = time


def average_waiting_time(append, pop):
    stats = defaultdict(list)
    stats[-1] = [0, 0]
    for a_frame, p_frame in zip(sorted(append, key=lambda p: p[2].id), sorted(pop, key=lambda p: p[2].id)):
        waiting_time = p_frame[0] - a_frame[0]
        tmp = stats[a_frame[2].priority]
        if tmp.__len__() == 0:
            tmp.append(0)
            tmp.append(0)
        tmp[0] += waiting_time
        tmp[1] += 1
        tmp = stats[-1]
        tmp[0] += waiting_time
        tmp[1] += 1
    return {key: value[0] / value[1] for key, value in sorted(stats.items())}


def standard_deviation_waiting_time(append, pop, _average_waiting_time):
    stats = defaultdict(list)
    stats[-1] = [0, 0]
    for a_frame, p_frame in zip(sorted(append, key=lambda p: p[2].id), sorted(pop, key=lambda p: p[2].id)):
        waiting_time = p_frame[0] - a_frame[0]
        tmp = stats[a_frame[2].priority]
        if tmp.__len__() == 0:
            tmp.append(0)
            tmp.append(0)
        tmp[0] += pow(waiting_time - _average_waiting_time[a_frame[2].priority], 2)
        tmp[1] += 1
        tmp = stats[-1]
        tmp[0] += pow(waiting_time - _average_waiting_time[-1], 2)
        tmp[1] += 1
    return {key: value[0] / ((value[1] - 1) if value[1] > 1 else 1) for key, value in sorted(stats.items())}


def average_queue_length(data, runtime):
    queue_len = 0
    last_time = 0
    for frame in sorted(data, key=lambda p: p[0]):
        q_time = (frame[0] - last_time) / runtime
        last_time = frame[0]
        queue_len += q_time * frame[1]
    return queue_len


def standard_deviation_queue_length(data, _average_queue_length, runtime):
    queue_len = 0
    last_time = 0
    for frame in sorted(data, key=lambda p: p[0]):
        q_time = frame[0] - last_time
        last_time = frame[0]
        queue_len += q_time * pow(frame[1] - _average_queue_length, 2) / runtime
    return sqrt(queue_len)


# average size of frames ->received<-
def average_packet_size(append):
    frame_length = 0
    frame_count = append.__len__()
    for frame in append:
        frame_length += frame[2].__len__() / frame_count
    return frame_length


def standard_deviation_packet_size(append, _average_packet_size):
    frame_length = 0
    frame_count = append.__len__() - 1 if append.__len__() > 1 else 1
    for frame in append:
        frame_length += pow(frame[2].__len__() - _average_packet_size, 2) / frame_count
    return sqrt(frame_length)