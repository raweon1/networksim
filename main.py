from time import time

from simulation.core import *
from simulation.node import *
from simulation.switch import Switch
from simulation.switch_buffer import *
from simulation.generators import *
from simulation.simulation_wrapper import *


def foo():
    tmp = time()
    some_channel_types = {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792,
                          "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
    env = NetworkEnvironment(channel_types=some_channel_types, verbose=True, preemption_penalty_bytes=0,
                             min_preemption_bytes=250)
    builder = env.builder
    nodes = [Flow(env, "Flow-1", "Sink"), Switch(env, "Switch", buffer_type=Priority_FCFS_Scheduler, preemption=False, monitor=True),
             SinglePacket(env, "Sink", "Flow-1", 0, 0)]
    builder.append_nodes(*nodes).connect_nodes(nodes[0], nodes[1]).connect_nodes(nodes[1], nodes[2])
    runtime = 10000
    env.run(until=runtime)
    print(time() - tmp)
    for interface, module in nodes[1].interface_modules.items():
        parse_switch_buffer(module[0].data, runtime, interface, env.table[nodes[1].address][interface][2])


def some_package_generator(env, source, destination):
    payload = 750
    priority = 1
    for i in range(0, 500):
        yield MonitoredPackage(env, source, destination, payload, priority)


def foo2():
    while True:
        some_channel_types = {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792,
                              "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
        env = NetworkEnvironment(channel_types=some_channel_types, verbose=False, preemption_penalty_bytes=0,
                                 min_preemption_bytes=250)
        builder = env.builder
        pi = PackageInjector(env, "Injector", "Switch", 10,
                             exp_generator(1), some_package_generator(env, "Injector", "Sink"), True)
        nodes = [pi,
                 Switch(env, "Switch", buffer_type=Priority_FCFS_Scheduler, preemption=False, monitor=True),
                 Switch(env, "Switch-2", buffer_type=Priority_FCFS_Scheduler, preemption=False, monitor=True),
                 SinglePacket(env, "Sink", "broadcast", 0, 0)]
        builder.append_nodes(*nodes).connect_nodes(nodes[1], nodes[2]).connect_nodes(nodes[2], nodes[3])
        yield env
