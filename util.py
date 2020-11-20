from ipaddress import IPv4Address
from socket import socket
from typing import List

from gns3fy import Node, Project, Link

from config import config_custom


class Console:
    sock: socket

    def __init__(self, console_host, console_port):
        self.sock = socket()
        try:
            self.sock.connect((console_host, console_port))
        except ConnectionRefusedError:
            print("Vous devez lancer le projet GNS3 pour configurer les routeurs")
            exit(0)

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


def enumerate_nodes(gs, project_id) -> NodeRepo:
    mynodes = NodeRepo()
    router_i = 1
    for node in gs.get_nodes(project_id):
        obj = Node(project_id=project_id, node_id=node['node_id'], connector=gs)
        obj.get()
        obj.interfaces = []

        obj.router = obj.node_type == 'dynamips'
        obj.router_id = str(IPv4Address(router_i))  # génère un router-id en forme a.b.c.d
        router_i += 1

        mynodes.add(obj)
    return mynodes


def enumerate_links(gs, project_id, mynodes):
    in4 = 0
    liens = []
    for _link in gs.get_links(project_id):
        link = Link(connector=gs, project_id=project_id, link_id=_link['link_id'])
        link.get()
        lien = Lien(link.link_id)
        lien.interface_a = link.nodes[0]['label']['text']
        lien.side_a = mynodes.get(link.nodes[0]['node_id'])
        lien.side_b = mynodes.get(link.nodes[1]['node_id'])
        lien.interface_b = link.nodes[1]['label']['text']

        # le réseau IPv6 est basé sur la 3e partie de l'UUID du lien dans GNS3
        # l'hôte sideA aura comme ip ::10, l'hote sideB ::11
        lien.network6 = '2001:' + link.link_id.split('-')[3]
        lien.network4 = f"10.10.{in4}"
        in4 += 1

        lien.side_a.interfaces.append(Interface(True, lien))
        lien.side_b.interfaces.append(Interface(False, lien))
        liens.append(lien)
    return liens


MAGIC_SVG = '<!-- fait par le script -->'


# supprime les labels & dessins générés automatiquement
def delete_drawings(project: Project):
    if project.drawings is not None or True:
        for draw in project.drawings:
            s = draw['svg']
            if s.split('>', 1)[1].startswith(MAGIC_SVG):  # or not draw['locked']:
                project.update_drawing(drawing_id=draw['drawing_id'], locked=False)
                project.delete_drawing(drawing_id=draw['drawing_id'])


def display_subnets(project: Project, liens):
    # affiche les subnets entre routeurs
    for lien in liens:
        text = f"{lien.network4}.0/24\n{lien.network6}::/64"
        x = (lien.side_a.x + lien.side_b.x) // 2 - 25
        y = (lien.side_a.y + lien.side_b.y) // 2
        project.create_drawing(
            svg=f'<svg width="120" height="40">{MAGIC_SVG}<rect width="120" height="40" fill="#ffffff" fill-opacity="1.0" stroke-width="2" stroke="#000000"/></svg>',
            x=x, y=y, z=1, locked=True)
        project.create_drawing(
            svg=f'<svg width="39" height="30">{MAGIC_SVG}<text font-family="TypeWriter" font-size="10.0" font-weight="bold" fill="#346c59" stroke="#afafe1" stroke-width="100" fill-opacity="1.0">{text}\n</text>'
                + '</svg>',
            x=x, y=y, z=100, locked=True)


def display_router_ids(project: Project, nodes: List[Node]):
    # affiche les router-ids
    for node in nodes:
        if not node.router:
            continue
        x = node.x
        y = node.y + 10
        project.create_drawing(
            svg=f'<svg width="60" height="15">{MAGIC_SVG}<rect width="60" height="15" fill="#ffffff" fill-opacity="1.0"/></svg>',
            x=x, y=y, locked=True)
        project.create_drawing(
            svg=f'<svg width="100" height="15">{MAGIC_SVG}<text>{node.router_id}</text></svg>',
            x=x, y=y - 4, locked=True)


def get_extra_interface_conf(router_name: str, interface_name: str):
    try:
        return config_custom[router_name]['interfaces'][interface_name]['extra']
    except KeyError:
        return ''


def get_extra_global_conf(router_name: str):
    try:
        return config_custom[router_name]['extra']
    except KeyError:
        return ''


def get_is_interface_disabled(router_name: str, interface_name: str) -> bool:
    try:
        return config_custom[router_name]['interfaces'][interface_name]['disable']
    except KeyError:
        return False


def get_is_router_disabled(router_name: str):
    try:
        return config_custom[router_name]['disable']
    except KeyError:
        return False


def get_router_id_overriden(router_name: str):
    try:
        return config_custom[router_name]['router_id_override']
    except KeyError:
        return False
