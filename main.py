from time import time
import json

from simulation.core import *
from simulation.frame import *
from simulation.node import *
from simulation.switch import Switch, PriorityMap, TransmissionSelectionAlgorithmMap, TrafficClassBandwidthMap, \
    SwitchPortParam
from simulation.generators import *
from simulation.simulation_wrapper import *


def some_frame_generator(env, source, destination, payload=750, priority=1):
    while True:
        payload = env.random.uniform(250, 1300)
        yield MonitoredFrame(env, source, destination, payload, priority)


def foo4():
    while True:
        env = NetworkEnvironment(name="Test", seed=1337, verbose=False)
        builder = env.builder
        monitored_node = Flow2(env, "Source", some_frame_generator(env, "Source", "Sink", priority=0), monitor=True)
        sink = SinglePacket(env, "Sink", "broadcast", 0, 0)
        switch_param = SwitchPortParam(1)
        switch_param.tsa_map.\
            map_traffic_class_transmission_selection_algorithm(0, TransmissionSelectionAlgorithmMap.credit_based_shaper)
        switch_param.tsa_bandwidth.map_traffic_class_bandwidth(0, 0.5)
        switch = Switch(env, "Switch", monitor=True, preemption=False)
        builder.append_nodes(monitored_node, switch, sink)
        builder.connect_nodes(monitored_node, switch, 10, None, 0, switch_param)
        builder.connect_nodes(switch, sink, 10, None, 0, switch_param)
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
simulate_same_multiple_csv(foo4(), 3, 100000, file_name="test")
