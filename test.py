import matplotlib.pyplot as plt
from main import foo3
from simulation.simulation_wrapper import *
from time import time
from threading import Thread, main_thread
from multiprocessing import Process, Queue


title = "average_package_latency"
# title = "standard_deviation_package_latency"


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


def run(x, y, z, b, c, d, e, q):
    gen = [foo3(i / 10, preemption=x, min_preemption_bytes=y, preemption_penalty_bytes=z) for i in range(1, 11)]
    start_time = time()
    result = simulate_multiple(gen, b, c, d)
    q.put((e, result))
    print("done in %0.2f s" % (time() - start_time))

#result = simulate_multiple([foo3(i / 10, preemption=False, min_preemption_bytes=1) for i in range(1, 11)], 15, runtime, 0.95)
#foo(result, "Preemption False")
#result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=1) for i in range(1, 11)], 15, runtime, 0.95)
#foo(result, "Preemption 1, 0")
#result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=250) for i in range(1, 11)], 15, runtime, 0.95)
#foo(result, "Preemption 250, 0")
#result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=500) for i in range(1, 11)], 15, runtime, 0.95)
#foo(result, "Preemption 500, 0")
#result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=1, preemption_penalty_bytes=8) for i in range(1, 11)], 15, runtime, 0.95)
#foo(result, "Preemption 1, 8")

if __name__ == '__main__':
    runtime = 1000000
    q = Queue()
    t1 = Process(target=run, args=(False, 1, 0, 30, runtime, 0.95, "Preemption False", q))
    t2 = Process(target=run, args=(True, 1, 0, 30, runtime, 0.95, "Preemption 1, 0", q))
    t3 = Process(target=run, args=(True, 250, 0, 30, runtime, 0.95, "Preemption 250, 0", q))
    t4 = Process(target=run, args=(True, 500, 0, 30, runtime, 0.95, "Preemption 500, 0", q))
    t5 = Process(target=run, args=(True, 1, 16, 30, runtime, 0.95, "Preemption 1, 16", q))
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
