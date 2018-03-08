from simulation.core import *
from simulation.node import Node
from simulation.switch_buffer import *
from simulation.switch_buffer import StrictPriorityAlgorithm, CreditBasedShaper


class PriorityMap(object):
    # number of available traffic classes x priority = traffic class
    # see 802.1Q page: 126
    map = [[0, 0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 1, 1, 1, 1],
           [0, 0, 0, 0, 1, 1, 2, 2],
           [0, 0, 1, 1, 2, 2, 3, 3],
           [0, 0, 1, 1, 2, 2, 3, 4],
           [1, 0, 2, 2, 3, 3, 4, 5],
           [1, 0, 2, 3, 4, 4, 5, 6],
           [1, 0, 2, 3, 4, 5, 6, 7]]

    def __init__(self, available_traffic_classes=8):
        self.available_traffic_classes = available_traffic_classes - 1

    # args = list of tuples of (priority, traffic_class)
    def map_priority_traffic_class(self, priority, traffic_class):
        self.map[self.available_traffic_classes][priority] = traffic_class

    def get_traffic_class(self, priority):
        return self.map[self.available_traffic_classes][priority]


class TransmissionSelectionAlgorithmMap(object):
    strict_priority = StrictPriorityAlgorithm
    credit_based_shaper = CreditBasedShaper

    def __init__(self, available_traffic_classes=8):
        self.transmission_selection_algorithm_per_traffic_class = []
        for i in range(0, available_traffic_classes):
            self.transmission_selection_algorithm_per_traffic_class.append(
                TransmissionSelectionAlgorithmMap.strict_priority)

    # arg = list of tuples of (traffic_class, transmission_selection_algorithm)
    def map_traffic_class_transmission_selection_algorithm(self, traffic_class, tsa):
        self.transmission_selection_algorithm_per_traffic_class[traffic_class] = tsa


class TrafficClassBandwidthMap(object):
    def __init__(self, available_traffic_classes=8):
        self.bandwidth_param = []
        for i in range(0, available_traffic_classes):
            self.bandwidth_param.append(0)

    # arg = list of tuples of (traffic_class, bandwidth usage in %)
    def map_traffic_class_bandwidth(self, traffic_class, delta_bandwidth):
        self.bandwidth_param[traffic_class] = delta_bandwidth


class SwitchPortParam(object):
    def __init__(self, available_traffic_classes=8):
        self.priority_map = PriorityMap(available_traffic_classes)
        self.tsa_map = TransmissionSelectionAlgorithmMap(available_traffic_classes)
        self.tsa_bandwidth = TrafficClassBandwidthMap(available_traffic_classes)


class Switch(Node):
    # aging_time in seconds
    def __init__(self, env, address, aging_time=-1, preemption=False, monitor=False):
        super(Switch, self).__init__(env, address, monitor)
        # time until entries in switch_table become invalid, input in seconds -> x1.000.000 for µs
        self.aging_time = aging_time * 1000000 if aging_time > 0 else aging_time
        # activate preemption for this Switch
        self.preemption = preemption
        # { source: port_in, time } = { destination: port_out, time }
        self.switch_table = {}
        # {port: [buffer, process] }
        # buffer and simpy.process for each port
        self.port_modules = {}
        # sleeping event if buffer is empty
        self.sleep_event = env.event()

    def on_frame_received(self, frame, port_in):
        self.env.sim_print("%s: %s received on port %s" % (str(self.address), str(frame), str(port_in)))
        # create entry in switch_table
        self.switch_table[frame.source] = [port_in, self.env.now]
        # valid switch_table entry -> add frame to buffer of port x
        # invalid switch_table entry -> broadcast frame
        # port_out = port_in -> discard frame
        try:
            destination_entry = self.switch_table[frame.destination]
            # entry to old | aging_time < 0 -> ignore aging_time
            if self.aging_time > 0 and self.env.now > destination_entry[1] + self.aging_time:
                self.broadcast_frame(frame, port_in)
                del self.switch_table[frame.destination]
            else:
                # destination_entry[0] = port_out
                if port_in == destination_entry[0]:
                    self.on_frame_discard(frame)
                else:
                    self.port_modules[destination_entry[0]][0].append_frame(frame)
                    self.port_modules[destination_entry[0]][1].interrupt("new frame")
        except KeyError:
            self.broadcast_frame(frame, port_in)

    def broadcast_frame(self, frame, source_port):
        self.env.sim_print("%s: %s broadcasting" % (str(self.address), str(frame)))
        for port, port_module in self.port_modules.items():
            # do not broadcast to source port
            if port != source_port:
                port_module[0].append_frame(frame)
                port_module[1].interrupt("new frame")

    def on_frame_discard(self, frame):
        self.env.sim_print("%s: %s discarded" % (str(self.address), str(frame)))

    # switch param = (PrioMap, TSAMap, TSAConfig)
    def on_port_added(self, port, bandwidth, *args):
        if args.__len__() == 0:
            switch_param = SwitchPortParam()
        else:
            switch_param = args[0]
        switch_buffer = SwitchBuffer(self.env, bandwidth, switch_param.priority_map, switch_param.tsa_map,
                                     switch_param.tsa_bandwidth, self.monitor)
        if self.preemption:
            self.port_modules[port] = [switch_buffer, self.env.process(
                self.preemption_run(port, switch_buffer))]
        else:
            self.port_modules[port] = [switch_buffer, self.env.process(self.run(port, switch_buffer))]

    def get_monitor_table(self):
        result = []
        for port, port_module in self.port_modules.items():
            switch_buffer = port_module[0]
            received_frames = switch_buffer.data["append"]
            transmitted_frames = switch_buffer.data["pop"]
            dropped_frames = switch_buffer.data["drop"]
            # [destination, port_in, bandwidth, physical_delay] }}
            connection_type = self.env.table[self.address][port]
            for frames, action_type in zip([received_frames, transmitted_frames, dropped_frames],
                                           ["received", "transmitted", "dropped"]):
                for frame_tuple in frames:
                    frame = frame_tuple[2]
                    tmp = {"sim_name": self.env.name, "sim_id": self.env.id, "sim_seed": self.env.seed,
                           "switch_address": self.address, "egress_port": port,
                           "d_trans": frame.__len__() * 8 / connection_type[2], "d_prop": connection_type[3],
                           "frame_id": frame.id, "frame_source": frame.source, "frame_destination": frame.destination,
                           "frame_size": frame.__len__(), "frame_traffic_class": frame.priority,
                           "action": action_type, "action_time": frame_tuple[0], "action_q_len": frame_tuple[1]}
                    result.append(tmp)
        return result

    def get_monitor_results(self):
        result = {}
        for port, port_module in self.port_modules.items():
            append = port_module[0].data["append"]
            pop = port_module[0].data["pop"]
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
            sub_result = {"frames_received": append.__len__(),
                          "frames_send": pop.__len__(),
                          "average_waiting_time": _average_waiting_time,
                          "standard_deviation_waiting_time": _standard_deviation_waiting_time,
                          "average_queue_length": _average_queue_length,
                          "standard_deviation_queue_length": _standard_deviation_queue_length,
                          "average_packet_size": _average_packet_size,
                          "standard_deviation_packet_size": _standard_deviation_packet_size}
            result[port] = sub_result
        return result

    def run(self, port, buffer):
        frame = None
        sending_event = None
        while True:
            try:
                if frame is not None:
                    if sending_event.processed:
                        # get new frame
                        frame = buffer.peek_next_frame()
                        if frame is not None:
                            sending_event = self.pop(frame, port)
                    else:
                        # wait until frame is transmitted
                        buffer.transmission_start(frame)
                        yield sending_event
                        buffer.transmission_done(frame)
                        self.env.sim_print("%s: %s send on port %s" %
                                           (str(self.address), str(frame), str(port)))
                elif not buffer.empty():
                    # there might be a new frame to transmit
                    frame = buffer.peek_next_frame()
                    if frame is not None:
                        sending_event = self.pop(frame, port)
                    else:
                        # no frame to transmit
                        yield self.sleep_event
                else:
                    # no frame to transmit
                    yield self.sleep_event
            except simpy.Interrupt:
                pass

    def preemption_run(self, port, buffer):
        pending_events = {}
        frame = None
        sending_event = None
        inspector = None
        while True:
            try:
                if frame is not None:
                    if sending_event.processed:
                        # get a new frame
                        frame = buffer.peek_next_frame()
                        if frame is not None:
                            try:
                                sending_event, inspector = pending_events[frame]
                                sending_event.interrupt("continue sending")
                                self.env.sim_print("%s: %s continued on port %s" %
                                                   (str(self.address), str(frame), str(port)))
                            except KeyError:
                                sending_event, inspector = self.pop(frame, port, inspector=True)
                    else:
                        buffer.transmission_start(frame)
                        yield sending_event
                        buffer.transmission_done(frame)
                        pending_events.pop(frame, None)
                        self.env.sim_print("%s: %s send on port %s" %
                                           (str(self.address), str(frame), str(port)))
                elif not buffer.empty():
                    # there might be a frame for transmission
                    frame = buffer.peek_next_frame()
                    if frame is not None:
                        try:
                            sending_event, inspector = pending_events[frame]
                            sending_event.interrupt("continue sending")
                            self.env.sim_print("%s: %s continued on port %s" %
                                               (str(self.address), str(frame), str(port)))
                        except KeyError:
                            sending_event, inspector = self.pop(frame, port, inspector=True)
                    else:
                        # there is no frame for transmission
                        yield self.sleep_event
                else:
                    # there is no frame for transmission
                    yield self.sleep_event
            except simpy.Interrupt:
                if frame is not None:
                    new_frame = buffer.peek_next_frame()
                    # inspector.process_interruptable() prevents a bug when we try to interrupt an event that would
                    # be processed at the same time (e.g. the frame will be sent at the same time)
                    if new_frame != frame and not sending_event.processed and inspector.process_interruptable():
                        pending_events[frame] = sending_event, inspector
                        sending_event.interrupt("stop sending")
                        buffer.transmission_pause(frame)
                        self.env.sim_print(
                            "%s: %s stopped on port %s" % (str(self.address), str(frame), str(port)))
                        frame = new_frame
                        # the receiver needs to know that a new frame is incoming (with a byte sequence)
                        # this is modeled by adding some extra bytes to this frame
                        sending_event, inspector = self.pop(frame, port,
                                                            extra_bytes=self.env.preemption_penalty_bytes,
                                                            inspector=True)
