from collections import deque, defaultdict
from math import sqrt


class SwitchBuffer(object):
    def next_frame(self):
        raise NotImplementedError("You have to implement this")

    def append_frame(self, frame):
        raise NotImplementedError("You have to implement this")

    # called when a frame is transmitted
    def remove(self, frame):
        raise NotImplementedError("You have to implement this")

    # called when a frame is dropped
    def drop_frame(self, frame):
        self.remove(frame)

    def empty(self):
        raise NotImplementedError("You have to implement this")

    def __len__(self):
        raise NotImplementedError("You have to implement this")


class MonitoredSwitchBuffer(SwitchBuffer):
    def __init__(self, env, switch_buffer, data=None):
        self.env = env
        self.to_monitor = switch_buffer
        self.data = data if data is not None else defaultdict(list)
        self.max_q_len = 0

    def next_frame(self):
        return self.to_monitor.next_frame()

    def append_frame(self, frame):
        self.to_monitor.append_frame(frame)
        self.data["append"].append((self.env.now, self.__len__(), frame))
        if self.to_monitor.__len__() > self.max_q_len:
            self.max_q_len = self.to_monitor.__len__()

    def remove(self, frame):
        self.data["pop"].append((self.env.now, self.__len__(), frame))
        self.to_monitor.remove(frame)

    def drop_frame(self, frame):
        self.data["drop"].append((self.env.now, self.__len__(), frame))
        self.to_monitor.drop_frame(frame)

    def empty(self):
        return self.to_monitor.empty()

    def __len__(self):
        return self.to_monitor.__len__()


class FCFS_Buffer(SwitchBuffer):
    def __init__(self):
        self.queue = deque([])

    def next_frame(self):
        return self.queue[0]

    def append_frame(self, frame):
        self.queue.append(frame)

    def remove(self, frame):
        self.queue.remove(frame)

    def empty(self):
        return self.queue.__len__() == 0

    def __len__(self):
        return self.queue.__len__()


class LCFS_Buffer(SwitchBuffer):
    def __init__(self):
        self.queue = []

    def next_frame(self):
        return self.queue[self.queue.__len__() - 1]

    def append_frame(self, frame):
        self.queue.append(frame)

    def remove(self, frame):
        self.queue.remove(frame)

    def empty(self):
        return self.queue.__len__() == 0

    def __len__(self):
        return self.queue.__len__()


class Priority_FCFS_Scheduler(SwitchBuffer):
    def __init__(self):
        self.queues = defaultdict(deque)
        self.max_priority = 0

    def next_frame(self):
        for i in range(0, self.max_priority + 1):
            try:
                return self.queues[i][0]
            except IndexError:
                pass
        return None

    def append_frame(self, frame):
        self.queues[frame.priority].append(frame)
        if frame.priority > self.max_priority:
            self.max_priority = frame.priority

    def remove(self, frame):
        self.queues[frame.priority].remove(frame)

    def empty(self):
        for queue in self.queues.values():
            if queue.__len__() > 0:
                return False
        return True

    def __len__(self):
        tmp = 0
        for queue in self.queues.values():
            tmp += queue.__len__()
        return tmp


# (time, queue_length, frame)
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


def parse_switch_buffer(buffer, runtime, port, bandwidth):
    data = buffer.data
    append = data["append"]
    pop = data["pop"]
    print()
    print("SwitchBuffer port %s" % str(port))
    print("Bandwidth:                               %d b/µs = Mb/s" % bandwidth)
    print("frames received                        %d" % append.__len__())
    print("frames send                            %d" % pop.__len__())

    # average_waiting_time = Zeit seid Betreten des Swichtes bis zum Verlassen (inklusive Übertragungsdauer)
    _average_waiting_time = average_waiting_time(append, pop)
    _standard_deviation_waiting_time = standard_deviation_waiting_time(append, pop, _average_waiting_time)

    _average_packet_size = average_packet_size(append)
    _standard_deviation_packet_size = standard_deviation_packet_size(append, _average_packet_size)

    append_pop = append + pop

    _average_queue_length = average_queue_length(append_pop, runtime)
    _standard_deviation_queue_length = standard_deviation_queue_length(append_pop, _average_queue_length, runtime)

    print("average frame size:                    %s Byte" % str(_average_packet_size))
    print("standard deviation frame size:         %s Byte" % str(_standard_deviation_packet_size))
    print("frame size / bandwidth:                %s µs" % str(_average_packet_size * 8 / bandwidth))
    print("average waiting time in µs:              %s" % str(_average_waiting_time))
    print("standard deviation waiting time:         %s" % str(_standard_deviation_waiting_time))
    print("average queue length:                    %s" % str(_average_queue_length))
    print("standard deviation queue length:         %s" % str(_standard_deviation_queue_length))
    print("Max queue length:                        %s" % buffer.max_q_len)
