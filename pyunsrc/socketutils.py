import socket
import select

class TimeoutError(Exception): pass

def new_udp_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def udp_listener_on(port, reuse_addr = True):
    s = new_udp_socket()
    if reuse_addr:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', port))
    return s

def wait_for_read(file_objs, timeout=None):
    l = select.select(file_objs, [], [], timeout)
    if l == ([], [], []):
        raise TimeoutError()
    return l[0]
