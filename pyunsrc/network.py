"""The Network module.

This is a generic Network Engine.

Features:
* A bunch of hosts can perform actions through the network objects such that they know for certain
  that all of their actions are pefromed *in sync* in all the hosts at the exact same iteration.
  These actions usually update each other about user inputs, and not about the progress which is
  individually calculated in each host.
* Based on UDP, very optimized for latency (not bandwidth). Though it can happily lose packets
  without causing lag or delay, until a certain threshold of packets is lost, in which case the
  network may "lag" until packets rearrive.
* Supports change of network parameters (such as the latency) in operation (as long as it is done
  via a synchronized action).
* Supports cross-Python-version and cross-platform networks.

Current Limitations:
* One Listener, multiple Connectors (only one "game host" can accept new connections)
* Handling one connection attempt at a time (Though this should be a short time as it only includes
  the time of sending connection request, until the host is part of the Network)
* Disconnections are not properly supported yet
* Probably does not scale up to many hosts very well (N**2 packets sent every iteration).

I hope to someday fix those limitations and add support for:
* Supernodes uniting data from several hosts and lowering the packet-overhead (Still N**2 data,
  but sent more efficiently in less packets) (Will this really help?)
"""

import socketutils
import socket
import errno
import random
from mymarshal import loads, dumps
from sets import Set as set
from Bunch import Bunch

class Error(Exception): pass
class ConnectionFailed(Error): pass
class RandomError(Error): pass

RECV_FRAME_TIMEOUT = 0.5
MAX_PACKET_SIZE = 32767
ATTEMPT_COUNT = 10

class Host(object):
    def __init__(self, id, name):
        self.name = name
        self.id = id
    def __cmp__(self, other):
        return cmp(self.id, other.id)
    def __hash__(self):
        return hash(self.id)

class LocalHost(Host):
    def __init__(self, id, name):
        super(LocalHost, self).__init__(id, name)
        self.actions_queue = {}
    def __repr__(self):
        return '<LocalHost>'
    def recv_actions(self, iteration_count):
        if iteration_count in self.actions_queue:
            actions = self.actions_queue[iteration_count]
            del self.actions_queue[iteration_count]
            return actions
        return []
    def send_actions(self, scheduled_iteration, iteration_count, actions):
        # If latency increased, then we may form "holes" here
        # If latency decreased, then we want to use the existing actions,
        # and not send any actions for a while
        if scheduled_iteration not in self.actions_queue:
            self.actions_queue[scheduled_iteration] = actions

class RemoteHost(Host):
    def __init__(self, id, name, address, sock):
        super(RemoteHost, self).__init__(id, name)
        self.address = address
        self.sock = sock
        self._tx_actions = {}
        self._rx_actions = {}
        self.is_disconnected = False
        
    def __repr__(self):
        return '<RemoteHost %r>' % (self.address,)
    
    def _send(self, frame):
        try:
            self.sock.send(dumps(frame))
        except socket.error, s:
            # Just "lose" the sent packet as any lost packet but remember that
            # we are a disconnected host
            self._handle_socket_error(s)
    
    def _handle_socket_error(self, s):
        sock_errno, errstr = s.args
        if sock_errno != errno.ECONNREFUSED:
            raise

        # This means that the host disconnected. Let us hope that it did
        # not lose any packets assymetrically ;)
        self.is_disconnected = True
            
    def _recv(self, timeout=RECV_FRAME_TIMEOUT):
        # Note that UDP receive will only receive from the correct
        # port due to the connect call from before
        socketutils.wait_for_read([self.sock], timeout=timeout)
        try:
            data = self.sock.recv(MAX_PACKET_SIZE)
        except socket.error, s:
            self._handle_socket_error(s)
            # Convert the disconnected error to another error that may occur
            # when disconnection occurs to unify the error handling.
            raise socketutils.TimeoutError()
        return loads(data)

    def _fill_actions_from_socket(self, iteration_count):
        frame_type, (executed_iteration_count, iterations) = self._recv()
        assert frame_type == 'Actions'

        for tx_iteration_count in self._tx_actions.keys():
            if tx_iteration_count <= executed_iteration_count:
                # This iteration was already executed on the remote side,
                # no need to send it anymore...
                del self._tx_actions[tx_iteration_count]

        for current_iteration_count, actions in iterations.iteritems():
            if current_iteration_count in self._rx_actions:
                assert self._rx_actions[current_iteration_count] == actions
            elif current_iteration_count >= iteration_count:
                self._rx_actions[current_iteration_count] = actions
    
    def send_actions(self, scheduled_iteration, iteration_count, cur_actions):
        if scheduled_iteration not in self._tx_actions:
            # If its already in, it means the latency was reduced and we need
            # not send this iteration.
            self._tx_actions[scheduled_iteration] = cur_actions
        
        self._last_sent_actions = ('Actions', (iteration_count, self._tx_actions))
        self._send(self._last_sent_actions)

    def resend_actions(self):
        self._send(self._last_sent_actions)
    
    def recv_actions(self, iteration_count):
        if iteration_count not in self._tx_actions:
            # This iteration does not really exist, because of a latency
            # increase
            return []
        while iteration_count not in self._rx_actions:
            self._fill_actions_from_socket(iteration_count)

        iteration_actions = self._rx_actions[iteration_count]

        # Discard old keys states
        for remote_iteration_count in self._rx_actions.keys():
            if remote_iteration_count <= iteration_count:
                del self._rx_actions[remote_iteration_count]

        return iteration_actions

class Network(object):
    def __init__(self, controller, local_name):
        host_id = random.randrange(0, 1L<<32)

        # Keep both a mapping of ID's to hosts and the sorted hosts list
        # so the various hosts can rely on the order of the list for their
        # operations.
        self.host_of_id = {}
        self.hosts = []
        self.remote_hosts = []
        
        self._tx_actions = {}
        self._rx_actions = []

        self._controller = controller

	self.iteration_count = 0
        self._setup_local_host(host_id, local_name)

        self.timeout_group = set()

    def random(self):
        if self._seed is None:
            raise RandomError('Network not initialized for random generation yet')
        x = random.WichmannHill(self._seed)
        self._seed = x.randrange(0, 1L<<32)
        return x

    def iteration_actions(self):
        iteration_actions = self._rx_actions
        self._rx_actions = []
        return iteration_actions

    def _setup_local_host(self, id, local_name):
        self.local_host = LocalHost(id, local_name)
        self._add_host(self.local_host)

    def notify(self, event, *args, **kw):
        args_str = ', '.join(map(str, args))
        kw_str = ', '.join(map(str, kw.items()))
        handler = getattr(self._controller, 'network__' + event, None)
        if handler is not None:
            handler(*args, **kw)

    def start_connecting(self):
        # TODO: Change this clause, instead use a notify when
        # publicized data is available.
        """Start the connection process to other hosts.

        By definition, after calling this method, publicized_data() is
        available.
        """
        raise NotImplementedError()

    def stop_connecting(self):
        """Stop the connection process to other hosts.

        Any connections in progress will be stopped."""
        raise NotImplementedError()

    def scheduled_iteration(self):
        return self.latency + self.iteration_count

    def run_action_on(self, host, action_name, *args):
        self._tx_actions.setdefault(host, []).append((action_name, args))

    def run_action_on_all(self, action_name, *args):
        for host in self.hosts:
            self.run_action_on(host, action_name, *args)

    def run_action_locally(self, action_name, *args):
        self.run_action_on(self.local_host, action_name, *args)

    def run_action_remotely(self, action_name, *args):
        for host in self.remote_hosts:
            self.run_action_on(host, action_name, *args)

    def _sync_actions(self):
        """Update the Network.

        Returns the actions to run this iteration."""

        assert self._rx_actions == []

        # TODO: Clean this code up such that all network-related stuff
        # (i.e TimeoutError) is in the host code or Network-subclass
        # code, and not here.

        latency = self.latency
        for host in self.hosts:
            host.send_actions(self.scheduled_iteration(),
                              self.iteration_count,
                              self._tx_actions.get(host, []))
        
        self._tx_actions.clear()

        hosts_still_missing = list(self.hosts)
        hosts_received = {}
        while hosts_still_missing:
            for host in hosts_still_missing[:]:
                try:
                    actions = host.recv_actions(self.iteration_count)
                except socketutils.TimeoutError:
                    if host not in self.timeout_group:
                        self.timeout_group.add(host)
                        self.notify('timeout_group_add', host)
                else:
                    if host in self.timeout_group:
                        self.timeout_group.remove(host)
                        self.notify('timeout_group_remove', host)
                    hosts_still_missing.remove(host)
                    hosts_received[host] = actions
            for host in hosts_still_missing:
                host.resend_actions()
            if hosts_still_missing:
                self.notify('timeout')

        def normal_actions(host):
            rx_actions_of_host = []
            for action_str, action_args in hosts_received[host]:
                internal_prefix = 'INTERNAL_'
                if action_str.startswith(internal_prefix):
                    method_name = '_action__%s' % (action_str[len(internal_prefix):],)
                    method = getattr(self, method_name)
                    method(host, *action_args)
                else:
                    rx_actions_of_host.append((action_str, action_args))
            return host, rx_actions_of_host

        # Replace the list with the new received actions
        # Some (INTERNAL) actions update self.hosts, so we want to iterate a
        # copy
        self._rx_actions = [normal_actions(host) for host in self.hosts[:]]

        self.notify('iteration_done')
        self.iteration_count += 1

    def _add_host(self, host):
        self.hosts.append(host)
        self.host_of_id[host.id] = host
        
        # Sort all hosts by the network-unique ID's, allowing
        # order-dependant algorithms
        self.hosts.sort()

        # Make sure host ID's are all unique
        assert len(self.host_of_id) == len(self.hosts), 'Known bug, please restart!'

        self.notify('host_added', host)

    def _remove_host(self, host):
        self.hosts.remove(remote_host)
        del self.host_of_id[remote_host.id]

        self.notify('host_removed', host)

    def _add_remote_host(self, remote_host):
        self.remote_hosts.append(remote_host)
        self._add_host(remote_host)

        self.notify('host_connected', remote_host)

    def _remove_remote_host(self, remote_host):
        self.remote_hosts.remove(remote_host)
        self._remove_host(remote_host)

    def _action__reset_random_seed(self, src_host):
        # A very clever random seed injection hack can use this action
        # A very very clever one, so clever it is impractical!
        # (Famous last words :)
        self._seed = self.iteration_count + sum([host.id for host in self.hosts])

    def _connect_to(self, src_host,
                    remote_host_id, remote_host_name,
                    original_remote_address, address):
        if not self._is_connecting:
            # Too late, his connection is aborted...
            return None
        
        sock = socketutils.new_udp_socket()
        sock.connect(address)
        remote_host = RemoteHost(remote_host_id, remote_host_name, address, sock)
        self._add_remote_host(remote_host)
        return remote_host

class Hoster(Network):
    def __init__(self, controller, local_name, publicized_data=None):
        super(Hoster, self).__init__(controller, local_name)
        self._publicized_data = publicized_data
        # Default initial latency
        self.latency = 0
        self._seed = random.randrange(0, 1L<<32)
    def publicized_data(self):
        return self._publicized_data
    def start_connecting(self):
        pass
    def stop_connecting(self):
        pass
    def update(self):
        self._sync_actions()

class Listener(Hoster):
    def __init__(self, controller, local_name, port,
                 protocol_version=None,
                 publicized_data=None):
        """host_id must be unique to this host"""
        super(Listener, self).__init__(controller, local_name, publicized_data)
        self._port = port
        self.protocol_version = protocol_version

        # Default initial latency
        self.latency = 1

        # Only after starting to connect
        self.update = None

        self._seed = None

    def _action__connect_to(self, src_host,
                            remote_host_id, remote_host_name,
                            original_remote_address, address):
        remote_host = self._connect_to(src_host,
                                       remote_host_id, remote_host_name,
                                       original_remote_address, address)
        if remote_host is None:
            return

        self._already_connected.append(original_remote_address)
        self._awaiting_connection = None

        # It is our job as Listener to reset everyone's random seed
        self.run_action_on_all('INTERNAL_reset_random_seed')
        self.notify('hosting_new_host', remote_host)

    def start_connecting(self):
        self._is_connecting = True
        self._listener_sock = socketutils.udp_listener_on(self._port)
        self._awaiting_connection = None
        self._already_connected = []
        self.update = self._attempt_listening

    def stop_connecting(self):
        self._is_connecting = False
        if self._awaiting_connection:
            unwelcome = 'NOTCONNECTING!', ()
            self._awaiting_connection.sock.send(dumps(unwelcome))
            # If the packet is lost, he'll keep on hammering me, but I
            # don't care...
        self._listener_sock.close()
        del self._listener_sock
        del self._awaiting_connection
        del self._already_connected
        self.update = self._sync_actions

    def _attempt_listening(self):
        self._sync_actions()
        
        if self._awaiting_connection is not None:
            # Cannot handle multiple connection requests at the same time
            return
        try:
            socketutils.wait_for_read([self._listener_sock], timeout=0)
        except socketutils.TimeoutError:
            return
        
        conn = Bunch()
        data, conn.remote_address = self._listener_sock.recvfrom(MAX_PACKET_SIZE)
        remote_hostname, remote_port = conn.remote_address
        remote_version, conn.remote_host_id, conn.remote_host_name = loads(data)
        assert remote_version == self.protocol_version, "Attempt to connect with client of different version"
        if conn.remote_address in self._already_connected:
            # We may be receiving a retransmit of the connection
            # packet from before, anyhow, he is already connected, so
            # ignore it.
            return
        
        self.notify("new_connector1", conn.remote_host_name, conn.remote_address)
        conn.sock=socketutils.new_udp_socket()
        conn.sock.connect(conn.remote_address)
        
        host_ids = [(host.id, host.name) for host in self.hosts]
        welcome_to_send = dumps(('WELCOME!', (self._publicized_data, host_ids)))
        conn._welcome_to_send = welcome_to_send
        conn._welcome_count = 0

        self._awaiting_connection = conn
        self.update = self._send_welcome

    def _send_welcome(self):
        self._sync_actions()
        
        conn = self._awaiting_connection
        remote_hostname, remote_port = conn.remote_address
        # Flood him with WELCOME!'s until he responds...
        conn.sock.send(conn._welcome_to_send)
        try:
            socketutils.wait_for_read([conn.sock], timeout=0.5)
        except socketutils.TimeoutError:
            conn._welcome_count += 1
            if conn._welcome_count >= ATTEMPT_COUNT:
                self.update = self._attempt_listening
                self._awaiting_connection = None
            return

        data = conn.sock.recv(MAX_PACKET_SIZE)
        request_type, ports = loads(data)
        assert request_type == 'listening_on'
        
        self.notify("new_connector2", conn.remote_host_name, conn.remote_address)
        for host, port in zip(self.hosts, ports):
            self.run_action_on(host, 'INTERNAL_connect_to',
                               conn.remote_host_id,
                               conn.remote_host_name,
                               conn.remote_address,
                               (remote_hostname, port))
        self.update = self._attempt_listening
        self._awaiting_connection = None

class Connector(Network):
    def __init__(self, controller, local_name, address, protocol_version=None):
        """host_id must be unique to this host"""
        super(Connector, self).__init__(controller, local_name)
        self.address = address
        self.protocol_version = protocol_version
        # Default initial latency
        self.latency = 1
        self._seed = None
    
    def publicized_data(self):
        if not hasattr(self, '_publicized_data'):
            raise NoPublicizedData()
        return self._publicized_data
    
    def start_connecting(self):
        print "Connecting to %s:%d" % self.address
        self._is_connecting = True
        
        self._socket_to_host = socketutils.new_udp_socket()

        for i in xrange(ATTEMPT_COUNT):
            # Send version to identify both our version and the local port of this connection
            self._socket_to_host.sendto(dumps((self.protocol_version,
                                               self.local_host.id,
                                               self.local_host.name)), self.address)
            # Receive hello as ack and to know the remote port of this particular connection
            try:
                socketutils.wait_for_read([self._socket_to_host], timeout=0.5)
            except socketutils.TimeoutError:
                pass
            else:
                request, remote_address = self._socket_to_host.recvfrom(MAX_PACKET_SIZE)
                request_type, request_data = loads(request)
                if request_type == 'NOTCONNECTING!':
                    raise ConnectionFailed("Other host has stopped connecting to us!")
                assert request_type == 'WELCOME!', "Expected WELCOME, received %r" % (request_type,)
                print "Received welcome response"
                self._publicized_data, host_ids = request_data

                # The welcome is sent from a different port (not the listening port)...
                self._socket_to_host.connect(remote_address)

                self._listener_socks = dict([(socketutils.udp_listener_on(0), (id, name))
                                             for id, name in host_ids])
                self._send_listening_on_ports()
                break
        else:
            raise ConnectionFailed("Cannot connect to given host")
        self.update = self._attempt_connecting

    def stop_connecting(self):
        self._is_connecting = False

        # TODO: Cut connection attempt
        # But until I do that, I better not allow stopping in middle...
        assert self.update == self._sync_actions

    def _send_listening_on_ports(self):
        ports = [sock.getsockname()[1] for sock in self._listener_socks]
        self._socket_to_host.send(dumps(('listening_on', ports)))

    def _attempt_connecting(self):
        try:
            all_files = [self._socket_to_host] + list(self._listener_socks)
            read_available = socketutils.wait_for_read(all_files, timeout=0)
        except socketutils.TimeoutError:
            return
        
        if read_available == [self._socket_to_host]:
            request, remote_address = self._socket_to_host.recvfrom(MAX_PACKET_SIZE)
            request_type, request_data = loads(request)
            # This can only be WELCOME because UNWELCOME cannot follow WELCOME
            assert request_type == 'WELCOME!', "Expected WELCOME, received %r" % (request_type,)
            # Hmm.. we are Welcome'd again... so appearantly he did not see we sent him our port list..
            self._send_listening_on_ports()
        else:
            # Somebody connects to us! This means that the entire network is in sync, and knows we're in!
            self.notify('got_first_connection')
            self._listen_to_all_create_remote_hosts()
            self.notify('in_network')
            self.update = self._sync_actions

    def _action__connect_to(self, src_host,
                            remote_host_id, remote_host_name,
                            original_remote_address, address):
        self._connect_to(src_host,
                         remote_host_id, remote_host_name,
                         original_remote_address, address)

    def _listen_to_all_create_remote_hosts(self):
        while self._listener_socks:
            read_available = socketutils.wait_for_read(list(self._listener_socks), timeout=60)
            for sock in read_available:
                remote_host_id, remote_host_name = self._listener_socks[sock]
                del self._listener_socks[sock]

                # Get the first Actions packet only to extract
                # iteration_count and the remote address
                
                data, address = sock.recvfrom(MAX_PACKET_SIZE)
                sock.connect(address)
                frame_type, (executed_iteration_count, iterations) = loads(data)
                assert frame_type == 'Actions'

                self.iteration_count = executed_iteration_count

                # Discard this Actions packet
                # It is okay because it is assumed to be losable and
                # because the next packet will contain all of its
                # actions again.

                # The first action set we receive MUST fix the random
                # seed (or we'll be out of sync)

                remote_host = RemoteHost(remote_host_id, remote_host_name, address, sock)
                self._add_remote_host(remote_host)
