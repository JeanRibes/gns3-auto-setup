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
    ip6_a: str  # # 2001:0:dead:beef::10
    interface_a: str

    network6: str  # 2001:0:dead:beef
    network4: str  # 10.0.8.

    interface_b: str
    ip6_b: str  # 2001:0:dead:beef::11
    side_b: Node

    def __str__(self):
        return f"{self.side_a.name}: {self.interface_a} [{self.get_ip6a()}] <-> [{self.get_ip6b()}] {self.interface_b}:{self.side_b.name}"

    def get_ip6a(self):
        return f"{self.network6}::10/64"

    def get_ip6b(self):
        return f"{self.network6}::11/64"


class Interface:
    def __init__(self, sa: bool, l: Lien):
        self.side_a = sa
        self.lien = l

    side_a: bool
    lien: Lien

    def get_ip6(self):
        if self.side_a:
            return self.lien.get_ip6a()
        else:
            return self.lien.get_ip6b()

    def get_ip4(self):
        """
        l'adresse IP finit en 2 pour sideA, en 1 pour sideB
        """
        return f"{self.lien.network4}.{int(self.side_a) + 1} 255.255.255.0"

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
