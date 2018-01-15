import matplotlib.pyplot as plt
from main import foo3
from simulation.simulation_wrapper import *
from time import time
from threading import Thread, main_thread
from multiprocessing import Process, Queue
from simulation.switch_buffer import *


# title = "average_package_latency"
# title = "standard_deviation_package_latency"
title = "average_waiting_time"


def foo(data, name=""):
    x = []
    y = []
    yerr = [list(), list()]
    for sim_name, sim_data in data.items():
        latency = sim_data["Source"][title]
        x.append(float(sim_name[11:]))
        y.append(latency["average"])
        yerr[0].append(latency["average"] - latency["lower"])
        yerr[1].append(latency["upper"] - latency["average"])
    plt.errorbar(x, y, yerr=yerr, label=name)
    return x, y, yerr


def bar(data, name=""):
    x = defaultdict(list)
    y = defaultdict(list)
    yerr = defaultdict(list)
    for sim_name, sim_data in data.items():
        for priority, latency in sim_data["Switch"][2][title].items():
            x[priority].append(float(sim_name[11:]))
            y[priority].append(latency["average"])
            yerr[priority].append(latency["average"] - latency["lower"])
    for key in x:
        plt.errorbar(x[key], y[key], yerr=yerr[key], label="%s %s" % (name, str(key)))


def run(x, y, z, swb, max_i, b, c, d, e, q):
    gen = [foo3(i / 10, switch_buffer=swb, preemption=x, min_preemption_bytes=y, preemption_penalty_bytes=z) for i in range(1, max_i * 10)]
    start_time = time()
    result = simulate_multiple(gen, b, c, d)
    q.put((e, result))
    print("done in %0.2f s" % (time() - start_time))


# result = simulate_multiple([foo3(i / 10, preemption=False, min_preemption_bytes=1) for i in range(1, 11)], 15, runtime, 0.95)
# foo(result, "Preemption False")
# result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=1) for i in range(1, 11)], 15, runtime, 0.95)
# foo(result, "Preemption 1, 0")
# result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=250) for i in range(1, 11)], 15, runtime, 0.95)
# foo(result, "Preemption 250, 0")
# result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=500) for i in range(1, 11)], 15, runtime, 0.95)
# foo(result, "Preemption 500, 0")
# result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=1, preemption_penalty_bytes=8) for i in range(1, 11)], 15, runtime, 0.95)
# foo(result, "Preemption 1, 8")


def a():
    if __name__ == '__main__':
        runtime = 1000000
        q = Queue()
        t1 = Process(target=run, args=(False, 1, 0, Priority_FCFS_Scheduler, 1, 30, runtime, 0.95, "Preemption False", q))
        t2 = Process(target=run, args=(True, 1, 0, Priority_FCFS_Scheduler, 1, 30, runtime, 0.95, "Preemption 1, 0", q))
        t3 = Process(target=run, args=(True, 250, 0, Priority_FCFS_Scheduler, 1, 30, runtime, 0.95, "Preemption 250, 0", q))
        t4 = Process(target=run, args=(True, 500, 0, Priority_FCFS_Scheduler, 1, 30, runtime, 0.95, "Preemption 500, 0", q))
        t5 = Process(target=run, args=(True, 1, 16, Priority_FCFS_Scheduler, 1, 30, runtime, 0.95, "Preemption 1, 16", q))
        threads = [t1, t2, t3, t4, t5]

        for thread in threads:
            thread.start()
        start_time = time()
        for thread in threads:
            result = q.get()
            foo(result[1], result[0])
        for thread in threads:
            thread.join()
        print("all done in %0.2f" % (time() - start_time))
        plt.title(title)
        plt.xlabel("intensity")
        plt.xticks([i / 10 for i in range(1, 11)])
        plt.ylabel("latency in µs")
        plt.legend()
        plt.savefig("preemption_%s.pdf" % title)
        plt.show()


def c():
    if __name__ == '__main__':
        runtime = 1000000
        q = Queue()
        t1 = Process(target=run, args=(False, 1, 0, Priority_FCFS_Scheduler, 1, 16, runtime, 0.95, "Priority_FCFS_Scheduler", q))
        t2 = Process(target=run, args=(False, 1, 0, FCFS_Buffer, 1, 16, runtime, 0.95, "FCFS_Buffer", q))
        t3 = Process(target=run, args=(False, 1, 0, LCFS_Buffer, 1, 16, runtime, 0.95, "LCFS_Buffer", q))
        # t4 = Process(target=run, args=(False, 1, 0, 16, runtime, 0.95, "Preemption 500, 0", q))
        # t5 = Process(target=run, args=(False, 1, 16, 16, runtime, 0.95, "Preemption 1, 16", q))
        threads = [t1, t2, t3]

        for thread in threads:
            thread.start()
        start_time = time()
        for thread in threads:
            result = q.get()
            bar(result[1], result[0])
        for thread in threads:
            thread.join()
        print("all done in %0.2f" % (time() - start_time))
        plt.title(title)
        plt.xlabel("intensity")
        plt.xticks([i / 10 for i in range(1, 11)])
        plt.ylabel("latency in µs")
        plt.legend()
        plt.savefig("preemption_%s.pdf" % title)
        plt.show()


def callback_foo(sim_env, x, y):
    x.append(sim_env.now)
    # y.append(sim_env.get_monitor_results()["Source"][title])
    y.append(sim_env.get_monitor_results()["Switch"][2][title][-1])


def b(intensity=0.5):
    x = []
    y = []
    simulate_in_steps(foo3(intensity, switch_buffer=FCFS_Buffer), 100, 100000, callback_foo, args=(x, y))
    plt.xlabel("sim_time")
    plt.ylabel("%s in µs" % title)
    plt.plot(x, y)
    plt.show()


c()

