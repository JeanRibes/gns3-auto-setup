import ipaddress
from ipaddress import IPv4Address
from typing import *

import gns3fy

from util import *

config_custom = { # permet
    'R8': {
        'disable': False,
        'extra': "ipv6 router rip OUI\nredistribute connected",
        'interfaces': {
            'f2/0': {
                'disable': False,
                'extra': "ipv6 address 2001:0:8::1/64"
            },
            'f3/0': {
                'disable': False,
            },
            'f0/0': {
                'disable': False,
            }
        }
    }
}


def get_extra_interface_conf(router_name: str, interface_name: str):
    try:
        return config_custom[router_name]['interfaces'][interface_name]['extra']
    except:
        print('err0')
        return ''

def get_extra_global_conf(router_name:str):
    try:
        return config_custom[router_name]['extra']
    except: return ''

def get_is_interface_disabled(router_name: str, interface_name: str) -> bool:
    try:
        return config_custom[router_name]['interfaces'][interface_name]['disable']
    except:
        return False


def get_is_router_disabled(router_name: str):
    try:
        return config_custom[router_name]['disable']
    except:
        return False


def make_config(router: Node, area: str, ospf_process: int = 1) -> str:


    s = f"""###### config pour {router.name} ######
ipv6 unicast-routing
router ospfv3 {ospf_process}
    address-family ipv6 unicast
        redistribute connected
        exit-address-family
    router-id {router.router_id}
  exit
{get_extra_global_conf(router.name)}
end
conf t"""

    for interface in router.interfaces:
        if get_is_interface_disabled(router.name,interface.get_name()):
            continue
        s += f"""
int {interface.get_name()}
# connectee a l'interface {interface.reverse_int()} du routeur {interface.reverse_router().name}
    no shut
    ipv6 enable
    ipv6 address {interface.get_ip()}
    """
        if interface.reverse_router().router:
            s += f"ipv6 ospf {ospf_process} area {area}\n"
        extra_conf_int = get_extra_interface_conf(router.name, interface.get_name())
        if len(extra_conf_int)>1:
            s += extra_conf_int +"\nend\nconf t"  # pour éviter les problèmes
        else:
            s += "exit"

    s += f"""
end
###### fin de la config pour {router.name} ######
    """

    return s


def apply_config(router: Node, config: str):
    if get_is_router_disabled(router.name):
        return None
    console: Console = router.vty
    console.write_cmd(b'\r')  # active la console
    console.write_cmd(b'end')
    console.write_cmd(b'configure terminal')
    console.write_conf(config)


if __name__ == '__main__':
    gs = gns3fy.Gns3Connector("http://localhost:3080", user="admin",
                              cred="YwrGQJnK6KPO7scnYIxTYiLpVmKc0VKeKwQEo9wMBP6D2oUdMCRJbt1AAh0Sts39")
    project_id = gs.get_project(name="test-python-autoconfig")['project_id']
    #    project_id = gs.get_project(name="nas-mpls")['project_id']

    mynodes = NodeRepo()
    # setup initial
    router_i = 0
    for node in gs.get_nodes(project_id):
        obj = gns3fy.Node(project_id=project_id, node_id=node['node_id'], connector=gs)
        obj.get()
        myconsole = Console(obj.console_host, obj.console)

        obj.vty = myconsole
        obj.interfaces = []

        obj.router = obj.node_type == 'dynamips'
        obj.router_id = str(IPv4Address(router_i))  # génère un router-id en forme a.b.c.d
        router_i += 1

        mynodes.add(obj)

    for _link in gs.get_links(project_id):
        link = gns3fy.Link(connector=gs, project_id=project_id, link_id=_link['link_id'])
        link.get()
        lien = Lien(link.link_id)
        lien.interface_a = link.nodes[0]['label']['text']
        lien.side_a = mynodes.get(link.nodes[0]['node_id'])
        lien.side_b = mynodes.get(link.nodes[1]['node_id'])
        lien.interface_b = link.nodes[1]['label']['text']

        lien.network = '2001:' + link.link_id.split('-')[3]

        lien.side_a.interfaces.append(Interface(True, lien))
        lien.side_b.interfaces.append(Interface(False, lien))

        print(lien)

    r8 = mynodes.get_by_name('R8')
    print(make_config(r8, '0', 9999))
    exit(0)
    for node in mynodes.values():
        if node.router:
            cfg = make_config(node, "0")
            print(f"configuration de {node.name} ... ", end="")
            apply_config(node, cfg)
            print("fini !")
