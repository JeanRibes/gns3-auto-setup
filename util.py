from socket import socket
from typing import Optional

from gns3fy import Node
from gns3fy.gns3fy import Config


class Console:
    sock: socket

    # consoel_port = Node().console
    def __init__(self, console_host, console_port):
        self.sock = socket()
        self.sock.connect((console_host, console_port))
        self.sock.recvfrom(100000)

    def write_conf(self, text: str):
        self.sock.send(text.replace('\n', '\r').encode('ascii'))

    def write_cmd(self, cmd: bytes):
        self.sock.send(cmd + b'\r')


class NodeRepo(dict):
    def get_by_name(self, name: str):
        for node in self:
            if node.name == name:
                return node

    def add(self, node: Node):
        self[node.node_id] = node


class JLink:
    link_id = 0
    source_int: str
    source_node: Node
    dest_int: str
    dest_node: Node
    network: Optional[str]
