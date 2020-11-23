import json
from dataclasses import dataclass
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import List, Union

import yaml
from gns3fy import Node
from jsonschema import validate


@dataclass
class Router:
    name: str
    x: int
    y: int
    uid: str
    router_id: str
    asn: int

    console_host: str
    console_port: int

    # type: List[Interface]
    interfaces: list

    @staticmethod
    def from_node(node: Node, ri,asn):
        return Router(name=node.name,
                      x=node.x, y=node.y, uid=node.node_id,
                      console_host=node.console_host, console_port=node.console,
                      router_id=ri, interfaces=[],asn=asn)


class Routers(dict):
    # type: List[Router]
    def get_by_uid(self, uid: str) -> Router:
        for router in self.values():
            if router.uid == uid:
                return router

    def add(self, router: Router):
        self[router.name] = router

    def __getitem__(self, item) -> Router:
        return super().__getitem__(item)


@dataclass
class Lien:
    uid: str

    network4: IPv4Address  # 10.2.0
    network6: str  # 2201:beef

    side_a: Router
    side_b: Router

    int_a: str
    int_b: str

    @property
    def interface_a(self):
        # type: () -> Interface
        return list(filter(lambda i: i.name == self.int_a, self.side_a.interfaces))[0]

    @property
    def interface_b(self):
        # type: () -> Interface
        return list(filter(lambda i: i.name == self.int_b, self.side_b.interfaces))[0]

    def __str__(self):
        return f"({self.side_a.name}) {self.int_a} <--> {self.int_b} ({self.side_b.name})"

    @property
    def name(self):
        return f"{self.side_a.name}<-->{self.side_b.name}"


SIDE_A = 'a'
SIDE_B = 'b'


@dataclass
class Interface:
    name: str
    lien: Union[Lien, None] = None  # si None, le lien n'est pas branché à un routeur
    side: str = 'u'  # 'a' ou 'b' ou 'u' si lien==None

    @property
    def peer(self) -> Router:
        if self.lien is not None:
            if self.side == 'a':
                return self.lien.side_b
            elif self.side == 'b':
                return self.lien.side_a
        return None

    @property
    def peer_int(self) -> str:
        if self.lien is not None:
            if self.side == 'a':
                return self.lien.int_b
            elif self.side == 'b':
                return self.lien.int_a
        return None

    @property
    def peer_interface(self):
        # type: () -> Interface
        if self.lien is not None:
            if self.side == 'a':
                return self.lien.interface_b
            elif self.side == 'b':
                return self.lien.interface_a
        return None

    @property
    def router(self) -> Router:
        if self.lien is not None:
            if self.side == 'b':
                return self.lien.side_b
            elif self.side == 'a':
                return self.lien.side_a
        return None

    def __str__(self):
        if self.lien is not None:
            return str(self.lien)
        return self.name

    def get_ip6(self):
        return f"{self.lien.network6}::{ord(self.side) - 96}"

    def get_ip_end(self) -> int:
        # 1 pour side_a, 2 pour side_b
        return ord(self.side) - 96

    def get_ip4(self):
        # on fait de la magie avec les IPv4 pour utiliser des sous-réseaux de 2 hôtes
        return f"{IPv4Address(int(self.lien.network4) + ord(self.side) - 96)}"




def load_user_conf(filename='user_conf.yaml')->dict:
    user_conf = yaml.load(open(filename,'r'), Loader=yaml.FullLoader)
    user_conf_schema = json.load(open('user-conf-schema.json', 'r'))
    validate(instance=user_conf, schema=user_conf_schema)
    return user_conf