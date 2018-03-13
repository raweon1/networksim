class Frame(object):
    """
    package to be sent
    each package has a payload - which is the number of bytes with application information
    each package has at least one header (multiple headers may be stacked) - each header is a tuple of (size, data)
        where size is the number of bytes of this header and data is some data the header contains
        this can be used to encapsulate a frame in another one
    each package has a source - which is an unique identifier of a node in the system
    each package has a destination - which is an unique identifier of a node in the system
    each package has a priority
    each package has an automatically generated id
    """
    def __init__(self, env, source, destination, payload: int, priority: int = 0, header = (26, "Ethernet_Frame_Header")):
        """

        :param env: NetworkEnvironment for this Frame
        :param source: Source-Node address!
        :param destination: Destination-Node address!
        :param payload: Size of the Payload in Bytes
        :param priority: Priority of this Frame. Should be 0-7
        :param header: default size of 26 Bytes.
        """
        self.id = env.get_frame_id()
        self.env = env
        self.source = source
        self.destination = destination
        self.payload = payload
        self.headers = []
        self.append_header(header)
        self.priority = priority

    def on_hop(self, sender, receiver):
        """
        called when this frame is received
        :param sender: sending node of this hop
        :param receiver: receiving node of this hop
        """
        pass

    def on_destination_reached(self, node):
        """
        called when this frame reached its destination node
        :param node: destination node
        """
        pass

    def peek_header(self):
        if self.headers.__len__() == 0:
            raise HeaderException("%s has no header" % str(self))
        return self.headers[self.headers.__len__() - 1]

    def pop_header(self):
        if self.headers.__len__() == 0:
            raise HeaderException("%s has no header" % str(self))
        return self.headers.pop()

    def append_header(self, header):
        self.headers.append(header)
        return self

    def __len__(self):
        t_len = self.payload
        for header in self.headers:
            t_len += header[0]
        return t_len

    def __str__(self):
        return "Frame(%d): (source: %s, dest: %s, size: %d, prio: %d)" % \
               (self.id, str(self.source), str(self.destination), self.__len__(), self.priority)


class HeaderException(Exception):
    pass


class MonitoredFrame(Frame):
    def __init__(self, *args, **kwargs):
        super(MonitoredFrame, self).__init__(*args, **kwargs)
        self.start_time = self.env.now
        self.latency = -1
        self.hops = QuickDirtyTree(time=self.env.now)

    def on_hop(self, sender, receiver):
        self.hops.append(sender.address, receiver.address, self.env.now)

    def on_destination_reached(self, node):
        self.latency = self.env.now - self.start_time

    def get_hop_table(self):
        result = []
        hop_table = self.hops.get_hop_table()
        frame = {"sim_name": self.env.name, "sim_id": self.env.id, "sim_seed": self.env.seed,
                 "frame_id": self.id, "frame_source": self.source, "frame_destination": self.destination,
                 "frame_size": self.__len__(), "frame_traffic_class": self.priority,
                 "frame_start_time": self.hops.time}
        # { (address_a, address_b) = [bandwidth, physical_delay] }
        connection_type_table = self.env.builder.table2
        for hop in hop_table:
            connection_type = connection_type_table[(hop["frame_hop_sender"], hop["frame_hop_receiver"])]
            d_trans = self.__len__() * 8 / connection_type[0]
            d_prop = connection_type[1]
            d_nodal = hop["frame_hop_receiver_time"] - hop["frame_hop_sender_time"]
            hop_things = {"d_trans": d_trans,
                          "d_prop": d_prop,
                          "d_queue": d_nodal - d_trans - d_prop,
                          "d_nodal": d_nodal,
                          "latency": hop["frame_hop_receiver_time"] - self.hops.time}
            result.append({**frame, **hop, **hop_things})
        return result


class QuickDirtyTree(object):
    def __init__(self, node=None, time=None):
        self.node_address = node
        self.time = time
        self.children = []

    def append(self, sender_address, receiver_address, time):
        if self.node_address is None:
            self.node_address = sender_address
        if self.node_address == sender_address:
            self.children.append(QuickDirtyTree(receiver_address, time))
        else:
            for child in self.children:
                child.append(sender_address, receiver_address, time)

    def get_hop_table(self, hop_count=0):
        hops = []
        for child in self.children:
            hops.append({"frame_hop_count": hop_count, "frame_last_hop": True,
                         "frame_hop_sender": self.node_address, "frame_hop_sender_time": self.time,
                         "frame_hop_receiver": child.node_address, "frame_hop_receiver_time": child.time})
            child_table = child.get_hop_table(hop_count + 1)
            if child_table.__len__() > 0:
                hops[-1]["frame_last_hop"] = False
                hops += child_table
        return hops
