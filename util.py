from socket import socket
from typing import Optional

from gns3fy import Node


class Console:
    sock: socket
    def __init__(self, console_host, console_port):
        self.sock = socket()
        try:
            self.sock.connect((console_host, console_port))
        except ConnectionRefusedError:
            print("Vous devez lancer le projet GNS3 pour configurer les routeurs")
            exit(0)
        self.sock.recvfrom(100000)

    def write_conf(self, text: str):
        # on remplace \n par \r car la console Cisco attend \r comme saut de ligne
        self.sock.send(text.replace('\n', '\r').encode('ascii'))

    def write_cmd(self, cmd: bytes):
        self.sock.send(cmd + b'\r')


class NodeRepo(dict):
    def get_by_name(self, name: str):
        for node in self.values():
            if node.name == name:
                return node

    def add(self, node: Node):
        self[node.node_id] = node

class Lien:
    def __init__(self, lid):
        self.link_id = lid

    link_id: str

    side_a: Node
    ip_a: str  # # 2001:0:dead:beef::10
    interface_a: str

    network: str  # 2001:0:dead:beef

    interface_b: str
    ip_b: str  # 2001:0:dead:beef::11
    side_b: Node

    def __str__(self):
        return f"{self.side_a.name}: {self.interface_a} [{self.get_ipa()}] <-> [{self.get_ipb()}] {self.interface_b}:{self.side_b.name}"

    def get_ipa(self):
        return f"{self.network}::10/64"

    def get_ipb(self):
        return f"{self.network}::11/64"


class Interface:
    def __init__(self, sa: bool, l: Lien):
        self.side_a = sa
        self.lien = l

    side_a: bool
    lien: Lien

    def get_ip(self):
        if self.side_a:
            return self.lien.get_ipa()
        else:
            return self.lien.get_ipb()

    def get_name(self):
        if self.side_a:
            return self.lien.interface_a
        else:
            return self.lien.interface_b

    def reverse_int(self):
        if not self.side_a:
            return self.lien.interface_a
        else:
            return self.lien.interface_b

    def reverse_router(self):
        if not self.side_a:
            return self.lien.side_a
        else:
            return self.lien.side_b
