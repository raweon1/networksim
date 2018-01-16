from simulation.core import *
from simulation.node import Node
from simulation.switch_buffer import *


class Switch(Node):
    # aging_time in seconds
    def __init__(self, env, address, buffer_type=FCFS_Buffer, aging_time=-1, preemption=False, monitor=False):
        super(Switch, self).__init__(env, address, monitor)
        # must be a subclass of SwitchBuffer - iminterfaceant: cannot be an instance of SwitchBuffer!
        self.buffer_type = buffer_type
        # time until entries in switch_table become invalid, input in seconds -> x1.000.000 for µs
        self.aging_time = aging_time * 1000000 if aging_time > 0 else aging_time
        # activate preemption for this Switch
        self.preemption = preemption
        # { source: interface_in, time } = { destination: interface_out, time }
        self.switch_table = {}
        # {interface: [buffer, process] }
        # buffer and simpy.process for each interface
        self.interface_modules = {}
        # sleeping event if buffer is empty
        self.sleep_event = env.event()

    def on_package_received(self, package, interface_in):
        self.env.sim_print("%s: %s received on interface %s" % (str(self.address), str(package), str(interface_in)))
        if not self.stream_package(package):
            # create entry in switch_table
            self.switch_table[package.source] = [interface_in, self.env.now]
            # valid switch_table entry -> add package to buffer of interface x
            # invalid switch_table entry -> broadcast package
            # interface_out = interface_in -> discard package
            try:
                destination_entry = self.switch_table[package.destination]
                # entry to old | aging_time < 0 -> ignore aging_time
                if self.aging_time > 0 and self.env.now > destination_entry[1] + self.aging_time:
                    self.broadcast_package(package, interface_in)
                    del self.switch_table[package.destination]
                else:
                    # destination_entry[0] = interface_out
                    if interface_in == destination_entry[0]:
                        self.on_package_discard(package)
                    else:
                        self.interface_modules[destination_entry[0]][0].append_package(package)
                        self.interface_modules[destination_entry[0]][1].interrupt("new package")
            except KeyError:
                self.broadcast_package(package, interface_in)

    def stream_package(self, package):
        try:
            stream = self.env.streams[package.destination]
            interfaces = stream[self.address]
            for interface, pop in interfaces.items():
                if pop == 1:
                    self.interface_modules[interface][0].append_package(package)
                    self.interface_modules[interface][1].interrupt("new package")
            return True
        except KeyError:
            return False

    def broadcast_package(self, package, source_interface):
        self.env.sim_print("%s: %s broadcasting" % (str(self.address), str(package)))
        for interface, interface_module in self.interface_modules.items():
            # do not broadcast to source interface
            if interface != source_interface:
                interface_module[0].append_package(package)
                interface_module[1].interrupt("new package")

    def on_package_discard(self, package):
        self.env.sim_print("%s: %s discarded" % (str(self.address), str(package)))

    def on_interface_added(self, interface):
        if self.monitor:
            switch_buffer = MonitoredSwitchBuffer(self.env, self.buffer_type())
        else:
            switch_buffer = self.buffer_type()
        if self.preemption:
            self.interface_modules[interface] = [switch_buffer, self.env.process(
                self.preemption_run(interface, switch_buffer))]
        else:
            self.interface_modules[interface] = [switch_buffer, self.env.process(self.run(interface, switch_buffer))]

    def get_monitor_results(self):
        result = {}
        for interface, interface_module in self.interface_modules.items():
            append = interface_module[0].data["append"]
            pop = interface_module[0].data["pop"]
            if append.__len__() > 0:
                if pop.__len__() > 0:
                    # average_waiting_time = Zeit seid Betreten des Swichtes bis zum Verlassen
                    # (inklusive Übertragungsdauer)
                    _average_waiting_time = average_waiting_time(append, pop)
                    _standard_deviation_waiting_time = standard_deviation_waiting_time(append, pop,
                                                                                       _average_waiting_time)
                else:
                    _average_waiting_time = -1
                    _standard_deviation_waiting_time = -1
                _average_packet_size = average_packet_size(append)
                _standard_deviation_packet_size = standard_deviation_packet_size(append, _average_packet_size)

                append_pop = append + pop

                _average_queue_length = average_queue_length(append_pop, self.env.now)
                _standard_deviation_queue_length = standard_deviation_queue_length(append_pop, _average_queue_length,
                                                                                   self.env.now)
            else:
                _average_waiting_time = -1
                _standard_deviation_waiting_time = -1
                _average_packet_size = -1
                _standard_deviation_packet_size = -1
                _average_queue_length = -1
                _standard_deviation_queue_length = -1
            sub_result = {"packages_received": append.__len__(),
                          "packages_send": pop.__len__(),
                          "average_waiting_time": _average_waiting_time,
                          "standard_deviation_waiting_time": _standard_deviation_waiting_time,
                          "average_queue_length": _average_queue_length,
                          "standard_deviation_queue_length": _standard_deviation_queue_length,
                          "average_packet_size": _average_packet_size,
                          "standard_deviation_packet_size": _standard_deviation_packet_size}
            result[interface] = sub_result
        return result

    def run(self, interface, buffer):
        package = None
        if buffer.empty():
            try:
                yield self.sleep_event
            except simpy.Interrupt:
                package = buffer.next_package()
                sending_event = self.pop(package, interface)
        else:
            package = buffer.next_package()
            sending_event = self.pop(package, interface)
        while True:
            try:
                if not buffer.empty() or not sending_event.processed:
                    if sending_event.processed:
                        package = buffer.next_package()
                        sending_event = self.pop(package, interface)
                    yield sending_event
                    self.env.sim_print("%s: %s send on interface %s" %
                                       (str(self.address), str(package), str(interface)))
                    buffer.remove(package)
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                pass

    def preemption_run(self, interface, buffer):
        pending_events = {}
        sending_package = None
        inspector = None
        if buffer.empty():
            try:
                yield self.sleep_event
            except simpy.Interrupt:
                sending_package = buffer.next_package()
                sending_event, inspector = self.pop(sending_package, interface, inspector=True)
        else:
            sending_package = buffer.next_package()
            sending_event, inspector = self.pop(sending_package, interface, inspector=True)
        while True:
            try:
                if not buffer.empty() or not sending_event.processed:
                    if sending_event.processed:
                        sending_package = buffer.next_package()
                        try:
                            sending_event, inspector = pending_events[sending_package]
                            sending_event.interrupt("continue sending")
                            self.env.sim_print("%s: %s continued on interface %s" %
                                               (str(self.address), str(sending_package), str(interface)))
                        except KeyError:
                            sending_event, inspector = self.pop(sending_package, interface, inspector=True)
                    yield sending_event
                    self.env.sim_print("%s: %s send on interface %s" %
                                       (str(self.address), str(sending_package), str(interface)))
                    pending_events.pop(sending_package, None)
                    buffer.remove(sending_package)
                else:
                    yield self.sleep_event
            except simpy.Interrupt:
                package = buffer.next_package()
                # inspector.finish_time - self.env.now > 50 prevents a bug when we try to interrupt an event that would
                # be processed at the same time (e.g. the package will be sent at the same time)
                # and it isn't useful to interrupt a package which will be finished in sub 50 µs
                if package != sending_package and not sending_event.processed and inspector.process_interruptable():
                    pending_events[sending_package] = sending_event, inspector
                    sending_event.interrupt("stop sending")
                    self.env.sim_print(
                        "%s: %s stopped on interface %s" % (str(self.address), str(sending_package), str(interface)))
                    sending_package = package
                    # the receiver needs to know that a new package is incoming (with a byte sequence)
                    # this is modeled by adding some extra bytes to this package
                    sending_event, inspector = self.pop(sending_package, interface,
                                                        extra_bytes=self.env.preemption_penalty_bytes,
                                                        inspector=True)
