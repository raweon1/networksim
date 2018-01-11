from collections import deque, defaultdict
from math import sqrt


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


class MonitoredSwitchBuffer(SwitchBuffer):
    def __init__(self, env, switch_buffer, data=None):
        self.env = env
        self.to_monitor = switch_buffer
        self.data = data if data is not None else defaultdict(list)

    def next_package(self):
        return self.to_monitor.next_package()

    def append_package(self, package):
        self.data["append"].append((self.env.now, self.__len__(), package))
        self.to_monitor.append_package(package)

    def remove(self, package):
        self.data["pop"].append((self.env.now, self.__len__(), package))
        self.to_monitor.remove(package)

    def empty(self):
        return self.to_monitor.empty()

    def __len__(self):
        return self.to_monitor.__len__()


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


class Priority_FCFS_Scheduler(SwitchBuffer):
    def __init__(self):
        self.queues = defaultdict(deque)
        self.max_priority = 0

    def next_package(self):
        for i in range(0, self.max_priority + 1):
            try:
                return self.queues[i][0]
            except IndexError:
                pass
        return None

    def append_package(self, package):
        self.queues[package.priority].append(package)
        if package.priority > self.max_priority:
            self.max_priority = package.priority

    def remove(self, package):
        self.queues[package.priority].remove(package)

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


# (time, queue_length, package)
def average_waiting_time(append, pop):
    stats = defaultdict(list)
    stats[-1] = [0, 0]
    for a_package, p_package in zip(sorted(append, key=lambda p: p[2].id), sorted(pop, key=lambda p: p[2].id)):
        waiting_time = p_package[0] - a_package[0]
        tmp = stats[a_package[2].priority]
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
    for a_package, p_package in zip(sorted(append, key=lambda p: p[2].id), sorted(pop, key=lambda p: p[2].id)):
        waiting_time = p_package[0] - a_package[0]
        tmp = stats[a_package[2].priority]
        if tmp.__len__() == 0:
            tmp.append(0)
            tmp.append(0)
        tmp[0] += pow(waiting_time - _average_waiting_time[a_package[2].priority], 2)
        tmp[1] += 1
        tmp = stats[-1]
        tmp[0] += pow(waiting_time - _average_waiting_time[-1], 2)
        tmp[1] += 1
    return [(key, sqrt(value[0] / value[1])) for key, value in sorted(stats.items())]


def average_queue_length(data, runtime):
    queue_len = 0
    last_time = 0
    for package in sorted(data, key=lambda p: p[0]):
        q_time = package[0] - last_time
        last_time = package[0]
        queue_len += q_time * package[1]
    return queue_len / runtime


def standard_deviation_queue_length(data, _average_queue_length, runtime):
    queue_len = 0
    last_time = 0
    for package in sorted(data, key=lambda p: p[0]):
        q_time = package[0] - last_time
        last_time = package[0]
        queue_len += q_time * pow(package[1] - _average_queue_length, 2)
    return sqrt(queue_len / runtime)


# average size of packages ->send<-
def average_packet_size(pop):
    package_length = 0
    package_count = pop.__len__()
    for package in pop:
        package_length += package[2].__len__() / package_count
    return package_length


def standard_deviation_packet_size(pop, _average_packet_size):
    package_length = 0
    package_count = pop.__len__()
    for package in pop:
        package_length += pow(package[2].__len__() - _average_packet_size, 2) / package_count
    return sqrt(package_length)


def parse(data, runtime, interface, bandwidth):
    append = data["append"]
    pop = data["pop"]

    # average_waiting_time = Zeit seid Betreten des Swichtes bis zum Verlassen (inklusive Übertragungsdauer)
    _average_waiting_time = average_waiting_time(append, pop)
    _standard_deviation_waiting_time = standard_deviation_waiting_time(append, pop, _average_waiting_time)

    _average_packet_size = average_packet_size(pop)
    _standard_deviation_packet_size = standard_deviation_packet_size(pop, _average_packet_size)

    append_pop = append + pop

    _average_queue_length = average_queue_length(append_pop, runtime)
    _standard_deviation_queue_length = standard_deviation_queue_length(append_pop, _average_queue_length, runtime)

    print("SwitchBuffer interface %s" % str(interface))
    print("Bandwidth:                           %d b/µs = Mb/s" % bandwidth)
    print("average package size:                %s Byte" % str(_average_packet_size))
    print("standard deviation package size:     %s" % str(_standard_deviation_packet_size))
    print("average waiting time:                %s" % str(_average_waiting_time))
    print("standard deviation waiting time:     %s" % str(_standard_deviation_waiting_time))
    print("average queue length:                %s" % str(_average_queue_length))
    print("standard deviation queue length:     %s" % str(_standard_deviation_queue_length))