from time import time
import json

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
    nodes = [Flow(env, "Flow-1", "Sink"),
             Switch(env, "Switch", buffer_type=Priority_FCFS_Scheduler, preemption=False, monitor=True),
             SinglePacket(env, "Sink", "Flow-1", 0, 0)]
    builder.append_nodes(*nodes).connect_nodes(nodes[0], nodes[1]).connect_nodes(nodes[1], nodes[2])
    runtime = 10000
    env.run(until=runtime)
    print(time() - tmp)
    for port, module in nodes[1].port_modules.items():
        parse_switch_buffer(module[0].data, runtime, port, env.table[nodes[1].address][port][2])


def some_frame_generator(env, source, destination, payload=750, priority=1):
    while True:
        payload = env.random.uniform(250, 1300)
        yield MonitoredFrame(env, source, destination, payload, priority)


def foo2():
    while True:
        some_channel_types = {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792,
                              "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
        env = NetworkEnvironment(channel_types=some_channel_types, verbose=False, preemption_penalty_bytes=0,
                                 min_preemption_bytes=250, seed=1337)
        builder = env.builder
        pi = FrameInjector(env, "Injector", "Switch-1", 10,
                           exp_generator(env, 1), some_frame_generator(env, "Injector", "Sink"), True)
        nodes = [pi,
                 Switch(env, "Switch-1", buffer_type=Priority_FCFS_Scheduler, preemption=False, monitor=True),
                 Switch(env, "Switch-2", buffer_type=Priority_FCFS_Scheduler, preemption=False, monitor=False),
                 SinglePacket(env, "Sink-1", "broadcast", 0, 0)]
        builder.append_nodes(*nodes).connect_nodes(nodes[1], nodes[2]).connect_nodes(nodes[2], nodes[3])
        yield env


def foo3(intensity, switch_buffer=Priority_FCFS_Scheduler, bandwidth=10, preemption=False, min_preemption_bytes=250,
         preemption_penalty_bytes=0):
    while True:
        some_channel_types = {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792,
                              "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
        env = NetworkEnvironment(name="intensity: %0.2f" % intensity, seed=1337,
                                 channel_types=some_channel_types, verbose=False,
                                 preemption_penalty_bytes=preemption_penalty_bytes,
                                 min_preemption_bytes=min_preemption_bytes)
        builder = env.builder
        monitored_node = Flow2(env, "Source", some_frame_generator(env, "Source", "Sink", priority=0), monitor=True)
        jitter_injector = FrameInjector(env, "Jitter", "Switch", bandwidth, exp_generator(env, intensity),
                                        some_frame_generator(env, "Injector", "Sink", priority=1), False)
        switch = Switch(env, "Switch", buffer_type=switch_buffer, preemption=preemption, monitor=True)
        sink = SinglePacket(env, "Sink", "broadcast", 0, 0)
        builder.append_nodes(monitored_node, jitter_injector, switch, sink)
        builder.connect_nodes(monitored_node, switch, bandwidth)
        builder.connect_nodes(switch, sink, bandwidth=bandwidth * 2)
        yield env


def nice_output(sim_env):
    print("-----------------------")
    print(json.dumps(sim_env.get_monitor_results(), indent=2))

# simulate_in_steps(foo2(), 10, 100000, nice_output)
# result = simulate_same_multiple(foo2(), 15, 1000000, 0.95)
# print(json.dumps(result, indent=2))

# result = simulate_same_multiple(foo3(0.5), 15, 1000000, 0.95)
# print(result)
# result = simulate_multiple([foo3(i / 10, preemption=True, min_preemption_bytes=1) for i in range(1, 11)], 15, 1000000, 0.95)
# print(json.dumps(result, indent=2))


# simulate_same_multiple_csv(foo2(), 10, 100000, "foooo")
simulate_multiple_csv([foo3(i / 10) for i in range(1, 11)], 10, 1000000, "foo3")
