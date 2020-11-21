import json
from copy import deepcopy
from ipaddress import IPv4Address

from gns3fy import gns3fy, Node, Link

from config import config_custom
from data import *
from jinja2 import Template

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

        # if router_side_b is None:
        #    router_side_a.interfaces.append(Interface(name=link.nodes[0]['label']['text']))
        #    continue
        # elif router_side_a is None:
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
        # print("enumerating link " + str(lien))

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


def gen_tree(router: Router) -> dict:
    ifs = []
    for int in router.interfaces:
        interface: Interface = int
        ifs.append({
            'name': interface.name,
            'lien': interface.lien.name,
            'ip4': interface.get_ip4(),
            'ip6': interface.get_ip6(),
        })
    return {
        'name': router.name,
        'router_id': router.router_id,
        'interfaces': ifs
    }


def find(liste: list, k, v):
    return list(filter(lambda e: e[k] == v, liste))[0]


def recurse_class(classname) -> List[dict]:
    classe_parent = find(config_custom['classes'], 'name', classname)
    classes = [classe_parent]
    for classe in safe_get_value(classe_parent, [], 'classes'):
        try:
            classes.append(find(config_custom['classes'], 'name', classe))
        except:
            pass
    return classes


def resolve_classes(classe_names: List[str]) -> List[dict]:
    l = []
    for classe_name in classe_names:
        l.extend(recurse_class(classe_name))
    l = deepcopy(l)
    for classe in l:
        classe.pop('classes', None)
    return l


def safe_get_value(data: dict, default, *args):
    try:
        obj = data
        for path in args:
            obj = obj[path]
        return obj
    except KeyError:
        return default
    except Exception as e:
        raise e
        return default


def apply_values(classes: List[dict], obj: dict):
    # rajoute les variables définies dans les classes
    for classe in classes:
        obj.update(safe_get_value(classe, {}, 'values'))


def resolve_link_config(router_a_name: str, router_b_name: str) -> dict:
    try:
        for link in config_custom['links']:
            if link['name'] == (router_a_name + '<-->' + router_b_name) or link['name'] == (
                    router_b_name + '<-->' + router_a_name):
                return link
        return None
    except KeyError:
        return None


def resolve_router_config(router: Router):
    conf = gen_tree(router)
    template = f"#configuration du routeur {router.name}"
    if config_custom['routers'].get(router.name):
        cc = config_custom['routers'][router.name]
        classes = resolve_classes(safe_get_value(cc, [], 'classes'))
        conf['disable'] = safe_get_value(cc, False, 'disable')
        apply_values(classes, conf)

        for interface in router.interfaces:
            int_conf = find(conf['interfaces'], 'name', interface.name)
            user_def_interface = safe_get_value(cc, {}, 'interfaces', interface.name)
            if_classes = resolve_classes(safe_get_value(user_def_interface, [], 'classes'))
            apply_values(if_classes, int_conf)

            lien = resolve_link_config(router.name, interface.peer.name)
            if lien is not None:
                link_classes = resolve_classes(safe_get_value(lien, [], 'interface_classes'))
                apply_values(link_classes, int_conf)

                router_classes = resolve_classes(safe_get_value(lien, [], 'router_classes'))
                apply_values(router_classes, conf)
                template += '\n' + safe_get_value(lien, '', 'template')
            template += '\n'+safe_get_value(user_def_interface,'','template')
        template += '\n'+safe_get_value(cc,'','template')
    conf['template'] = template

    return conf
    # except:
    #    print("ATTENTION: la configuration")
    #    return conf

def generate_conf(conf:dict)->str:
    return Template(conf['template']).render(conf)

if __name__ == '__main__':
    # print(safe_get_value(config_custom, 'fail', 'routers', 'R8', 'interfaces','f0/0','disable'))
    routers, gs, project_id, liens = get_gns_conf()
    r1: Router = routers.get('R2')

    # print(json.dumps(recurse_class('routeur-coeur'), indent=4, sort_keys=True))
    print(generate_conf(resolve_router_config(r1)))
