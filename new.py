from ipaddress import IPv4Address

from gns3fy import gns3fy, Node, Link
from data import *


def enumerate_routers(gs, project_id):
    routers = Routers()

    router_i = 1
    for node in gs.get_nodes(project_id):
        obj = Node(project_id=project_id, node_id=node['node_id'], connector=gs)
        obj.get()
        if obj.node_type == 'dynamips':
            routers.add(Router.from_node(obj, str(IPv4Address(router_i))))
            router_i += 1
    return routers


def enumerate_links(gs, project_id, routers: Routers):
    in4 = 0
    liens = []
    for _link in gs.get_links(project_id):
        link = Link(connector=gs, project_id=project_id, link_id=_link['link_id'])
        link.get()

        router_side_a = routers.get_by_uid(link.nodes[0]['node_id'])
        router_side_b = routers.get_by_uid(link.nodes[1]['node_id'])

        #if router_side_b is None:
        #    router_side_a.interfaces.append(Interface(name=link.nodes[0]['label']['text']))
        #    continue
        #elif router_side_a is None:
        #    router_side_b.interfaces.append(Interface(name=link.nodes[1]['label']['text']))
        #    continue

        lien = Lien(
            uid=link.link_id,
            network6='2001:' + link.link_id.split('-')[3],
            network4=f"10.10.{in4}",
            side_a=router_side_a, side_b=router_side_b,
            int_a=link.nodes[0]['label']['text'],
            int_b=link.nodes[1]['label']['text'],
        )
        in4 += 1
        print("enumerating link "+str(lien))

        side_a_interface = Interface(name=link.nodes[0]['label']['text'], lien=lien, side=SIDE_A)
        side_b_interface = Interface(name=link.nodes[1]['label']['text'], lien=lien, side=SIDE_B)

        # relie les deux interfaces ensembles
        side_a_interface.lien = lien
        side_b_interface.lien = lien

        # attache l'interface au routeur
        router_side_a.interfaces.append(side_a_interface)
        router_side_b.interfaces.append(side_b_interface)

        liens.append(lien)
    return liens


def get_gns_conf():
    gs = gns3fy.Gns3Connector("http://localhost:3080", user="admin")
    project_id = list(filter(lambda p: p['status'] == 'opened', gs.get_projects()))[0]['project_id']
    project = gns3fy.Project(project_id=project_id, connector=gs)
    project.get()

    routers = enumerate_routers(gs, project_id)
    liens = enumerate_links(gs, project_id, routers)
    return routers, gs, project_id, liens

def gen_tree(routers: Routers)->dict:
    d={}
    r:Router = 0
    for router in routers.values():
        d[router.name]={
            ''
        }

if __name__ == '__main__':
    routers, gs, project_id, liens = get_gns_conf()
    for l in liens:
        print(f"{l.side_a.name}:{l.int_a} <-> {l.int_b}:{l.side_b.name}   {l.network6}::/64")
    print("===")
    r1: Router = routers.get('R1')
    for i in r1.interfaces:
        print(f"{i.router.name}:{i.name} <-> {i.peer_int}:{i.peer.name}   {i.lien.network6}::/64")

    print(len(r1.interfaces))