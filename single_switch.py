import simpy
from collections import defaultdict, deque
import numpy as np
from math import sqrt


def sim_print(env, str):
    print("%0.2f:" % env.now + " " + str)


class Package(object):
    def __init__(self, id, size, destination, priority):
        self.id = id
        self.size = size
        self.destination = destination
        self.priority = priority

    def __str__(self):
        return "(%d %0.2f %d %d)" % (self.id, self.size, self.destination, self.priority)


class Scheduler(object):
    """
    Scheduler der das nächste zu versendene Packet ausgibt
    """
    def next_package(self):
        raise NotImplementedError("You have to implement this")

    def empty(self):
        raise NotImplementedError("You have to implement this")

    def append_package(self, package):
        raise NotImplementedError("You have to implement this")

    def __len__(self):
        raise NotImplementedError("You have to implement this")


class Monitored_Scheduler(Scheduler):

    def __init__(self, scheduler, env):
        self.to_monitor = scheduler
        self.env = env
        self.data = defaultdict(list)

    def next_package(self):
        package = self.to_monitor.next_package()
        if package is not None:
            self.data["pop"].append((self.env.now, self.__len__(), (package.id, package.priority)))
        return package

    def empty(self):
        return self.to_monitor.empty()

    def append_package(self, package):
        self.data["append"].append((self.env.now, self.__len__(), (package.id, package.priority)))
        return self.to_monitor.append_package(package)

    def __len__(self):
        return self.to_monitor.__len__()


class Priority_FCFS_Scheduler(Scheduler):
    def __init__(self):
        self.queues = defaultdict(deque)
        self.max_priority = 0

    def append_package(self, package):
        self.queues[package.priority].append(package)
        if package.priority > self.max_priority:
            self.max_priority = package.priority

    def empty(self):
        for queue in self.queues.values():
            if queue.__len__() > 0:
                return False
        return True

    def next_package(self):
        for i in range(0, self.max_priority + 1):
            try:
                return self.queues[i].popleft()
            except IndexError:
                pass
        return None

    def __len__(self):
        tmp = 0
        for queue in self.queues.values():
            tmp += queue.__len__()
        return tmp


class FCFS_Scheduler(Scheduler):
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


class LCFS_Scheduler(Scheduler):
    def __init__(self):
        self.queue = []

    def append_package(self, package):
        self.queue.append(package)

    def empty(self):
        return self.queue.__len__() == 0

    def next_package(self):
        return self.queue.pop()

    def __len__(self):
        return self.queue.__len__()


class Switch(object):
    """
    Switch empfängt Pakete und speichert diese 'put'
    Switch hat mehrere Ausgänge (output_count) die parallel Pakete verschicken können, jedoch steht für jedes Paket
        fest welchen Ausgang es nehmen muss (Routing im System)
    """
    def __init__(self, env, output_count, bandwidth):
        self.env = env
        """
        Erstellt einen Scheduler für jeden Ausgang den ein Paket nehmen kann, da die Ausgänge parallel senden können 
        aber nicht die Last eines anderen Ausgangs übernehmen können
        """
        self.scheduler = [Monitored_Scheduler(Priority_FCFS_Scheduler(), env) for i in range(0, output_count)]
        """
        Wake-up-Events für den Scheduler
        """
        self.events = [env.event() for i in range(0, output_count)]
        self.output_procs = [env.process(self.run(i, self.scheduler[i], bandwidth))
                             for i in range(0, output_count)]

    def put(self, package):
        self.scheduler[package.destination].append_package(package)
        """
        wake-up
        """
        self.events[package.destination].succeed()
        self.events[package.destination] = self.env.event()

    def run(self, id, scheduler, bandwidth):
        while True:
            if not scheduler.empty():
                package = scheduler.next_package()
                sim_print(self.env, "%d sending package " % id + str(package) +
                          " / time = %0.2f" % (package.size / bandwidth) +
                          " / queue = %d" % scheduler.__len__())
                yield self.env.timeout(package.size / bandwidth)
            else:
                sim_print(self.env, "%d sleeping / %d" % (id, scheduler.__len__()))
                yield self.events[id]


def send(env, switch):
    id = 0
    while True:
        id += 1
        size = abs(np.random.normal(500, 100))
        destination = np.random.randint(0, 1)
        priority = np.random.randint(0, 3)
        package = Package(id, size, destination, priority)
        sim_print(env, "new package " + str(package))
        switch.put(package)
        yield env.timeout(np.random.exponential(1.1))


def average_waiting_time(append, pop):
    stats = defaultdict(list)
    stats[-1] = [0, 0]
    for a_package, p_package in zip(sorted(append, key=lambda p: p[2][0]), sorted(pop, key=lambda p: p[2][0])):
        waiting_time = p_package[0] - a_package[0]
        tmp = stats[a_package[2][1]]
        if tmp.__len__() == 0:
            tmp.append(0)
            tmp.append(0)
        tmp[0] += waiting_time
        tmp[1] += 1
        tmp = stats[-1]
        tmp[0] += waiting_time
        tmp[1] += 1
    return [(key, value[0] / value[1]) for key, value in sorted(stats.items())]


def variance_waiting_time(append, pop, _average_waiting_time):
    stats = defaultdict(list)
    stats[-1] = [0, 0]
    for a_package, p_package in zip(sorted(append, key=lambda p: p[2][0]), sorted(pop, key=lambda p: p[2][0])):
        waiting_time = p_package[0] - a_package[0]
        tmp = stats[a_package[2][1]]
        if tmp.__len__() == 0:
            tmp.append(0)
            tmp.append(0)
        tmp[0] += pow(waiting_time - _average_waiting_time[a_package[2][1] + 1][1], 2)
        tmp[1] += 1
        tmp = stats[-1]
        tmp[0] += pow(waiting_time - _average_waiting_time[0][1], 2)
        tmp[1] += 1
    return [(key, sqrt(value[0] / value[1])) for key, value in sorted(stats.items())]


def average_queue_length(data):
    queue_len = [0, 0]
    last_time = 0
    for package in sorted(data, key=lambda p: p[0]):
        q_time = package[0] - last_time
        last_time = package[0]
        queue_len[0] += q_time * package[1]
        queue_len[1] += q_time
    return queue_len[0] / queue_len[1]


def variance_queue_length(data, _average_queue_length):
    queue_len = [0, 0]
    last_time = 0
    for package in sorted(data, key=lambda p: p[0]):
        q_time = package[0] - last_time
        last_time = package[0]
        queue_len[0] += q_time * pow(package[1] - _average_queue_length, 2)
        queue_len[1] += q_time
    return sqrt(queue_len[0] / queue_len[1])


def parse(data):
    append = data["append"]
    pop = data["pop"]

    _average_waiting_time = average_waiting_time(append, pop)
    _variance_waiting_time = variance_waiting_time(append, pop, _average_waiting_time)

    append_pop = append + pop

    _average_queue_length = average_queue_length(append_pop)
    _variance_queue_length = variance_queue_length(append_pop, _average_queue_length)

    print("average waiting time:\t" + str(_average_waiting_time))
    print("variance waiting time:\t" + str(_variance_waiting_time))
    print("average queue length:\t" + str(_average_queue_length))
    print("variance queue length:\t" + str(_variance_queue_length))


env = simpy.Environment()
switch = Switch(env, 3, 475)
proc = env.process(send(env, switch))
env.run(until=1000000)
print([switch.scheduler[i].__len__() for i in range(0, 3)])
#print([(key, val.__len__()) for key, val in sorted(switch.scheduler[0].to_monitor.queues.items())])
parse(switch.scheduler[0].data)
