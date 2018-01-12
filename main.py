from time import time

from simulation.core import *
from simulation.node import *
from simulation.switch import Switch
from simulation.switch_buffer import *

tmp = time()
some_channel_types = {"Fiber": 0.97 * 299.792, "Coaxial": 0.8 * 299.792,
                      "Copper": 0.6 * 299.792, "Radio": 0.2 * 299.792}
env = NetworkEnvironment(channel_types=some_channel_types, verbose=False, preemption_penalty_bytes=0,
                         min_preemption_bytes=250)
builder = env.builder
nodes = [Flow(env, "Flow-1", "Sink"), Switch(env, "Switch", buffer_type=Priority_FCFS_Scheduler, preemption=True, monitor=True),
         SinglePacket(env, "Sink", "Flow-1", 0, 0)]
builder.append_nodes(*nodes).connect_nodes(nodes[0], nodes[1]).connect_nodes(nodes[1], nodes[2])
runtime = 100000000
env.run(until=runtime)
print(time() - tmp)
for interface, module in nodes[1].interface_modules.items():
    parse(module[0].data, runtime, interface, env.table[nodes[1].address][interface][2])
