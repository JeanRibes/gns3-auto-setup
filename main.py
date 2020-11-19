from ipaddress import IPv4Address
from typing import *

import gns3fy

from util import *

if __name__ == '__main__':
    gs = gns3fy.Gns3Connector("http://localhost:3080", user="admin",
                              cred="YwrGQJnK6KPO7scnYIxTYiLpVmKc0VKeKwQEo9wMBP6D2oUdMCRJbt1AAh0Sts39")
    project_id = gs.get_project(name="nas-mpls")['project_id']

    mynodes = NodeRepo()
    # setup initial
    router_i = 0
    for node in gs.get_nodes(project_id):
        obj = gns3fy.Node(project_id=project_id, node_id=node['node_id'], connector=gs)
        obj.get()
        myconsole = Console(obj.console_host, obj.console)
        myconsole.write_cmd(b'\r')  # active la console

        obj.vty = myconsole

        obj.router = obj.node_type == 'dynamips'
        obj.router_id = str(IPv4Address(router_i))  # génère un router-id en forme a.b.c.d
        router_i += 1

        mynodes.add(obj)

    # mapping des connexions
    my_links = []
    i = 0
    for node_id, node in mynodes.items():
        jlinks = []
        print(f"{node.name} ({node.router_id})")
        for link in node.links:
            jlink = JLink()
            jlink.link_id = i
            i += 1
            for link_node in link.nodes:
                if link_node['node_id'] == node_id:
                    jlink.source_int = link_node['label']['text']
                    jlink.source_node = node
                else:
                    jlink.dest_int = link_node['label']['text']
                    jlink.dest_node = mynodes.get(link_node['node_id'])
            print(f"   ({jlink.source_node.name}):{jlink.source_int}  -->  {jlink.dest_int}:({jlink.dest_node.name})")

            jlinks.append(jlink)
            node.jlinks = jlinks
            my_links.append(jlink)

    # reduce des links
    for i, right_jlink in enumerate(my_links):
        print(f"#{right_jlink.link_id}   ({right_jlink.source_node.name}):{right_jlink.source_int}  -->  {right_jlink.dest_int}:({right_jlink.dest_node.name})")
        filt = lambda jlink:(jlink.dest_node.name == right_jlink.source_node.name) \
                            and jlink.dest_int == right_jlink.source_int
        for left_jlink in filter(filt,my_links):
            print(f"    #{left_jlink.link_id}   ({left_jlink.source_node.name}):{left_jlink.source_int}  -->  {left_jlink.dest_int}:({left_jlink.dest_node.name})")


