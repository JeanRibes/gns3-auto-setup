#!/usr/bin/env python3
import argparse
import ipaddress
import json
import os
import re
import sys
import time
import traceback
from copy import deepcopy
from socket import *
from typing import Set
from urllib.parse import urlparse

import requests
from jinja2 import Template
from gns3fy import gns3fy, Project, Link

from config import default_yaml
from data import *

user_config = {}
MAGIC_SVG = '<!-- fait par le script -->'


def construct_ipv4(network: str, end: int) -> str:
    """
    Construit une adresse IPv4 à partir du réseau et de l'adresse.
    Ce n'est pas juste une concaténation de strings, mais bien un calcul
    qui marche même avec des tailles de préfixes différentes de 8/16/24/32
    :param network: le réseau au format a.b.c.0
    :param end: un entier, exemple 1 pour faire a.b.c.1
    :return:
    """
    try:
        end = int(end)
        net = int(IPv4Address(network))
        return str(IPv4Address(net + end))
    except ipaddress.AddressValueError:
        return "erreur"


def enumerate_routers(gs, project_id):
    routers = Routers()

    router_i = 1
    asn = 101
    for node in gs.get_nodes(project_id):
        obj = Node(project_id=project_id, node_id=node['node_id'], connector=gs)
        obj.get()
        if obj.node_type == 'dynamips' or obj.symbol == ':/symbols/classic/router.svg':
            routers.add(Router.from_node(obj, str(IPv4Address(router_i)), asn=asn))
            router_i += 1
            asn += 1
    return routers


def enumerate_links(gs, project_id, routers: Routers) -> List[Lien]:
    in4 = 2887680000
    liens = []
    for _link in gs.get_links(project_id):
        link = Link(connector=gs, project_id=project_id, link_id=_link['link_id'])
        link.get()

        router_side_a = routers.get_by_uid(link.nodes[0]['node_id'])
        router_side_b = routers.get_by_uid(link.nodes[1]['node_id'])

        if router_side_a is None and router_side_b is None:
            continue

        if router_side_b is None:
            router_side_a.interfaces.append(Interface(name=link.nodes[0]['label']['text']))
            continue
        elif router_side_a is None:
            router_side_b.interfaces.append(Interface(name=link.nodes[1]['label']['text']))
            continue

        lien = Lien(
            uid=link.link_id,
            network6='2001:10:0:' + link.link_id.split('-')[3],
            network4=IPv4Address(in4),
            side_a=router_side_a, side_b=router_side_b,
            int_a=link.nodes[0]['label']['text'],
            int_b=link.nodes[1]['label']['text'],
        )
        in4 += 4
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
    # for lien in liens:
    #    print(f'{lien.side_a.name}>    {lien.network4}    <{lien.side_b.name}')
    #    # print(f'{lien.interface_a.get_ip4()} {lien.side_a.name}>    {lien.network4}    <{lien.side_b.name} {lien.interface_b.get_ip4()}')
    return liens


def get_gns_conf(url, password):
    if password is not None:
        gs = gns3fy.Gns3Connector(url, user="admin",cred=password)
    else:
        gs = gns3fy.Gns3Connector(url, user="admin")
    try:
        project_id = list(filter(lambda p: p['status'] == 'opened', gs.get_projects()))[0]['project_id']
    except requests.exceptions.ConnectionError as e:
        traceback.print_exc()
        print(
            "==============================================================================================================================",
            file=sys.stderr)
        print(
            "\nErreur: Impossible de se connecter à GNS3!\nVeuillez lancer le logiciel et/ou désactiver la protection par mot de passe",
            file=sys.stderr)
        exit(1)
    except IndexError:
        print("Erreur: Vous devez ouvrir exactement un projet GNS3",file=sys.stderr)
        exit(1)
    project = gns3fy.Project(project_id=project_id, connector=gs)
    project.get()

    routers = enumerate_routers(gs, project_id)
    liens = enumerate_links(gs, project_id, routers)
    return routers, gs, project_id, liens


def show_topology(routers: Routers):
    for router in routers.values():
        print(f"routeur {router.name}")
        for itf in router.interfaces:
            print(
                f" *   {itf.name} -> {itf.peer.name if itf.peer is not None else 'client'}: {itf.peer_int if itf.peer is not None else ''}")


def gen_tree(router: Router) -> dict:
    ifs = []
    for int in router.interfaces:
        interface: Interface = int
        if interface.peer is not None:  # un routeur de l'autre côté
            ifs.append({
                'name': interface.name,
                'lien': interface.lien.name,
                'ipv4_network': str(interface.lien.network4),
                'ipv4_netmask': '255.255.255.252',
                'ipv4_prefixlen': 30,
                'ipv6_network': str(interface.lien.network6),
                'ipv6_prefixlen': 64,
                'ip_end': interface.get_ip_end(),
                'uid': interface.lien.uid,
            })
        else:
            ifs.append({
                'name': interface.name,
                'lien': 'edge',
                'ipv4_network': 'configurez manuellement',
                'ipv6_network': 'configurez manuellement',
                'ip_end': '1',
            })
    return {
        'name': router.name,
        'router_id': router.router_id,
        'interfaces': ifs,
        'asn': router.asn,
    }


def find(liste: list, k, v):
    try:
        return list(filter(lambda e: e[k] == v, liste))[0]
    except IndexError:
        print(f"['{k}']={v} non trouvé !\n il vous manque sûrement la classe {v}")
        exit(1)


def find2(liste: list, k, v, default):
    try:
        return list(filter(lambda e: e[k] == v, liste))[0]
    except:
        return default


def r2(classnames: Set[str]) -> Set[str]:
    """
    Normalement il peut pas faire de RecursionError
    :param classnames: la liste des classes à étendre récursivement
    :return: toutes les classes découvertes+initiales
    """
    if len(classnames) == 0:
        return set()
    discovered = set()
    for classe in user_config['classes']:
        if classe['name'] in classnames:
            discovered.update(safe_get_value(classe, [], 'classes'))
    initial = set(classnames)
    nouveaux = discovered - initial
    if len(discovered) == 0 or len(nouveaux) == 0:
        return initial | discovered
    missing = r2(nouveaux)
    return initial | discovered | missing


def resolve_classes(classe_names: List[str], type) -> List[dict]:
    all_class_names = r2(set(classe_names))
    l = []
    for classe_name in all_class_names:
        classe_obj: dict = find(user_config['classes'], 'name', classe_name)
        if classe_obj['type'] == type:
            classe_obj = deepcopy(classe_obj)
            classe_obj.pop('classes', None)
            l.append(classe_obj)
    return l


def safe_get_value(data: dict, default, *args):
    try:
        obj = data
        for path in args:
            obj = obj[path]
        return obj
    except (KeyError, TypeError):
        return default
    except Exception as e:
        raise e
        return default


def apply_classes_values(classes: List[dict], obj: dict):
    # rajoute les variables définies dans les classes
    for classe in classes:
        obj.update(safe_get_value(classe, {}, 'values'))
        if not classe.get('template'):
            classe['template']=''


def add_templates(classes: List[dict]) -> str:
    t = ''
    for classe in classes:
        t += safe_get_value(classe, '', 'template')
    return t


def resolve_link_config(router_a_name: str, router_b_name: str) -> dict:
    try:
        for link in user_config['links']:
            if link['name'] == (router_a_name + '<-->' + router_b_name) or link['name'] == (
                    router_b_name + '<-->' + router_a_name):
                return link
        return None
    except (KeyError, AttributeError):
        return None


def resolve_router_config(router: Router) -> dict:
    """
    construit la config et fait le templating des templates (sans appliquer les valeurs)
    :param router:
    :return:
    """
    conf = gen_tree(router)
    template = safe_get_value(user_config, '', 'templates', 'router')
    cc = find2(user_config['routers'], 'name', router.name, {})
    classes = resolve_classes(safe_get_value(cc, [], 'classes') + user_config['default_router_classes'], 'router')
    apply_classes_values(classes, conf)

    if cc.get('values'):
        conf.update(cc['values'])
    conf['resolved_classes'] = classes

    conf['interface_classes'] = []
    for classe in filter(lambda c: c.get('interface_classes'), classes):
        conf['interface_classes'].extend(classe['interface_classes'])
    conf['disable'] = safe_get_value(cc, False, 'disable')

    for interface in router.interfaces:
        int_conf = find(conf['interfaces'], 'name', interface.name)  # la config auto-généré
        if cc.get('interfaces'):
            user_def_interface = find2(cc['interfaces'], 'name', interface.name, {})  # la config utilisateur
        else:
            user_def_interface = {}
        int_conf['disable'] = safe_get_value(user_def_interface, False, 'disable')
        if_classes = resolve_classes(
            safe_get_value(user_def_interface, [], 'classes')
            + user_config['default_interface_classes']
            + conf['interface_classes'] if interface.peer is not None else []  # fait en sorte
            # de ne pas configurer de protocole de routage sur une interface de bordure
            # les interfaces externes doivent être config à la main
            , 'interface')
        apply_classes_values(if_classes, int_conf)
        if user_def_interface.get('values'):
            int_conf.update(user_def_interface['values'])
        int_conf['resolved_classes'] = if_classes
        int_conf['template'] = safe_get_value(user_config, '', 'templates', 'interface')
        int_conf['interface_template'] = safe_get_value(user_def_interface, '', 'template')
        if interface.peer is not None:
            lien_custom = resolve_link_config(router.name, interface.peer.name)
            int_conf['peer'] = {
                'asn': interface.peer.asn,
                'ipv4': interface.peer_interface.get_ip4(),
                'ipv6': interface.peer_interface.get_ip6(),
                'name': interface.peer.name,
                'interface': interface.peer_int,
            }
        else:
            lien_custom = None
        if lien_custom is not None:  # ajoute des configurations personalisées à l'interface depuis la config des liens
            link_classes = resolve_classes(safe_get_value(lien_custom, [], 'interface_classes'), 'interface')
            apply_classes_values(link_classes, int_conf)
            int_conf['resolved_classes'] += link_classes
            router_classes = resolve_classes(safe_get_value(lien_custom, [], 'router_classes'), 'router')
            apply_classes_values(router_classes, conf)
            conf['resolved_classes'] += router_classes
            int_conf['interface_template'] += safe_get_value(lien_custom, '', 'template')

            if lien_custom.get('interface_values'):
                int_conf.update(lien_custom['interface_values'])
                interface.lien.network4_display = int_conf['ipv4_network']
            # re-mapping
        conf['template'] = '\n' + safe_get_value(cc, '', 'template') + add_templates(classes)
    conf['router_template'] = safe_get_value(cc, '', 'template')
    conf['template'] = template

    # re-mapping de la config utilisateur, pour les dessins GNS3
    router.router_id = conf['router_id']

    return conf
    # except:
    #    print("ATTENTION: la configuration")
    #    return conf


def generate_conf(conf: dict) -> str:
    #print(f"génération de la conf de {conf['name']}")
    conf_txt = open(f"output/conf_{conf['name']}.cfg", 'w+')
    conf_json = open(f"output/conf_{conf['name']}.json", 'w+')

    rendered = Template(conf['template']).render(
        Template=Template,
        router=conf,
        globals=safe_get_value(user_config, {}, 'globals'),
        construct_ipv4=construct_ipv4  # fontion qui permet de créer l'adresse IPv4 avec l'adresse réseau
    )

    # https://stackoverflow.com/questions/28901452/reduce-multiple-blank-lines-to-single-pythonically
    rendered = re.sub(r'\n\s*\n', '\n', rendered)

    conf_txt.write(rendered)
    conf_txt.close()
    json.dump(conf, conf_json, indent=4, sort_keys=True)
    conf_json.close()
    return rendered


class Console:
    sock: socket
    name: str

    def __init__(self, console_host, console_port, name=''):
        self.name = name
        self.sock = socket()
        try:
            print(console_host,console_port)
            self.sock.connect((console_host, console_port))
        except ConnectionRefusedError as e:
            print("Vous devez lancer le projet GNS3 pour configurer les routeurs")
            raise e

    def write_conf(self, text: str):
        # on remplace \n par \r car la console Cisco attend \r comme saut de ligne
        self.write_cmd(b'')
        self.write_cmd(b'configure terminal')
        self.sock.send(text.replace('\n', '\r').encode('utf-8'))
        self.write_cmd(b'\rend')

    def write_cmd(self, cmd: bytes):
        self.sock.send(cmd + b'\r')

    def reset_read(self):
        # sert à vider le buffer pour que la prochaine sortie console correspond à l'entrée récente
        self.sock.recv(10000000000)
        self.write_cmd(b'')
        time.sleep(0.1)
        self.sock.recv(100000)
        self.sock.settimeout(1)

    def read(self):
        t = self.sock.recv(100000)
        return t.decode('ascii', 'ignore')

    def exec_cmd(self, cmd: str):
        """
        Cette fonction exécute une commande sur le routeur et renvoie le résultat !
        c'est assez lent car basé sur des timeouts, vu que la console telnet de GNS3 n'est pas synchrone
        :param cmd:
        :return:
        """
        self.write_cmd(cmd.encode('ascii'))
        for i in range(10):
            self.write_cmd(b' ')  # appuie sur espace pour passer tout le `sh run`
        self.write_cmd(b'#fini')
        ret = ''
        while True:
            try:
                ret += self.read()
            except timeout:
                break
        ret = ret.split(self.name + '#', 1)[0]
        return ret

    @staticmethod
    def from_router(router: Router):
        return Console(console_host='127.0.0.1', console_port=router.console_port)


def configure_router(router: Router, conf: str, console: Console):
    print(f'configuration de  {router.name}')
    for partie in conf.split('#--'):
        console.write_conf(partie)
        time.sleep(0.5)
        print('.', end='')
        sys.stdout.flush()
    print(f"{router.name} configuré !")


def delete_drawings(project: Project):
    if project.drawings is not None:
        for draw in project.drawings:
            s = draw['svg']
            if s.split('>', 1)[1].startswith(MAGIC_SVG):  # or not draw['locked']:
                try:
                    project.update_drawing(drawing_id=draw['drawing_id'], locked=False)
                    project.delete_drawing(drawing_id=draw['drawing_id'])
                except Exception as e:
                    print(e.args)
                    pass


def display_tracked_subnets(project: Project, liens: List[Lien]):
    # affiche les subnets entre routeurs
    for lien in liens:
        text = f"{lien.network4_display}"
        x = (lien.side_a.x + lien.side_b.x) // 2 - 25
        y = (lien.side_a.y + lien.side_b.y) // 2
        try:
            project.create_drawing(
                svg=f'<svg width="125" height="40">{MAGIC_SVG}<rect width="125" height="40" fill="#ffffff" fill-opacity="1.0" stroke-width="2" stroke="#000000"/></svg>',
                x=x, y=y, z=1, locked=True)
            project.create_drawing(
                svg=f'<svg width="39" height="30">{MAGIC_SVG}<text font-family="TypeWriter" font-size="10.0" font-weight="bold" fill="#346c59" stroke="#afafe1" stroke-width="100" fill-opacity="1.0">{text}\n</text>'
                    + '</svg>',
                x=x, y=y, z=100, locked=True)
        except AttributeError:
            pass  # truc à la con de l'API gns3 qui arrive temps en temps


def display_router_ids(project: Project, routers: Routers):
    # affiche les router-ids et les ASN
    for node in routers.values():
        x = node.x
        y = node.y + 10
        try:
            project.create_drawing(
                svg=f'<svg width="60" height="15">{MAGIC_SVG}<rect width="60" height="15" fill="#ffffff" fill-opacity="1.0"/></svg>',
                x=x, y=y, locked=True)
            project.create_drawing(
                svg=f'<svg width="100" height="15">{MAGIC_SVG}<text>{node.router_id}\n   {node.asn}</text></svg>',
                x=x, y=y - 4, locked=True)
        except AttributeError: # des fois GNS3 est pas content
            pass


def display_costs(project: Project, routers: Routers):
    for router in routers.values():
        conf = resolve_router_config(router)
        for intf in conf['interfaces']:
            try:
                cost = intf['ospf6_cost']
                for ri in router.interfaces:
                    ro_int: Interface = ri
                    if ro_int.name == intf['name']:
                        peer = ro_int.peer
                x = int((router.x * 1.5 + peer.x * 0.5) / 2)
                y = int((router.y * 1.5 + peer.y * 0.5) / 2)
                project.create_drawing(
                    svg=f'<svg width="80" height="35">{MAGIC_SVG}<rect width="80" height="35" fill="#000000" fill-opacity="1.0"/></svg>',
                    x=x + 1, y=y + 5, locked=True)
                project.create_drawing(
                    svg=f'<svg width=\"39\" height=\"30\"><!-- fait par le script --><text font-family=\"TypeWriter\" font-size=\"10.0\" font-weight=\"bold\" fill=\"#ffffff\" stroke=\"#afafe1\" stroke-width=\"100\" fill-opacity=\"1.0\">ospf6_cost\n  {cost}</text></svg>',
                    x=x, y=y, locked=True)
            except KeyError:
                continue
            except Exception as e:
                raise e


def generate_skeleton(routers: List[Router], liens: List[Lien]) -> dict:
    links = []
    for lien in liens:
        links.append({
            'name': lien.name,
            'interface_classes': [],
            'router_classes': [],
            'template': "",
            'interface_values': {},
        })
    main = {
        'templates': {
            'router': "",
            'interface': "",
        },
        'default_router_classes': [],
        'default_interface_classes': [],
        'classes': [{
            'name': "<default>",
            'type': "<router|interface>",
            'template': "",
            'values': {
                'a': 'b',
            }
        }],
        'links': links,
        'routers': []
    }
    for router in routers:
        ifs = []
        for interface in router.interfaces:
            ifs.append({
                "name": interface.name,
                'template': "",
                'classes': [],
                'values': {},
            })
        main['routers'].append({
            "name": router.name,
            'disable': False,
            'classes': [],
            'template': "",
            'interfaces': ifs,
            'values': {},
        })
    return main

def gen_hosts_file(all_confs:dict):
    hosts_f=""
    for conf in all_confs:
        for interface in conf['interfaces']:
            try:
                hosts_f += f"{construct_ipv4(interface['ipv4_network'],interface['ip_end'])}   {conf['name']}\n"
                #hosts_f += f"{interface['ipv6_network']}::{interface['ip_end']}    {conf['name']}\n"
            except KeyError:
                pass
    return hosts_f

def parse_cli():
    parser = argparse.ArgumentParser(description='Configurateur automatique de routeurs dans GNS3')
    parser.add_argument('--gen-skeleton', '-k', action='store_true',
                        help="Affiche un squelette de configuration adapté au "
                             "réseau détécté, sans configurer les routeurs.")
    parser.add_argument('--hide-labels', '-n', action='store_false',
                        help="Crée des jolis labels dans GNS3 pour afficher "
                             "les subnets, router-id et ASN")
    parser.add_argument('--delete-labels', action='store_true', help="Efface tous les labels crées par ce programme"
                                                                     " de GNS3 puis termine.")
    parser.add_argument('--apply', '-a', action='store_true',
                        help="Active l'envoi automatique des configurations aux routeurs")
    parser.add_argument('--show-topology', '-s', action='store_true',
                        help="Montre la topologie détéctée par ce script.")
    parser.add_argument('--global-cmd', '-g', type=str, nargs='+', default=[], metavar='commande',
                        help='Une commande qui sera exécutée sur tous les routeurs en même temps. Pas besoin d\'utiliser de guillemets')
    parser.add_argument('--export-user-conf', '-e', action='store_true',
                        help="Exporte la configuration utilisateur au format JSON et termine")
    parser.add_argument('--import-user-conf', '-i', type=str, nargs=1, default=['user-conf.yaml'],
                        metavar='user-conf.yaml',
                        help="Utilise la configuration utilisateur depuis un fichier YAML")
    parser.add_argument('--gen-hosts','-o', action='store_true',
                        help="Affiche les lignes à rajouter au fichier /etc/hosts")
    #parser.add_argument('--gns-project-id',type=str,nargs=1,default='AUTO',metavar='gns3_project_name',
    #                    help="ID du projet GNS3 à utiliser. Par défaut, utilise celui qui est ouvert") #flemme
    parser.add_argument('--gns3-url','-u',type=str,nargs=1,default=['http://localhost:3080'])
    parser.add_argument('--gns3-password','-p',type=str,nargs=1,default=[None])
    vals = parser.parse_args()
    return vals


def init_files():
    try:
        open('user-conf.yaml', 'r')
    except FileNotFoundError:
        f = open('user-conf.yaml', 'w')
        f.write(default_yaml)
        f.close()

    try:
        os.mkdir('output')
    except FileExistsError:
        pass


if __name__ == '__main__':
    init_files()
    vals = parse_cli()
    gns3host = urlparse(vals.gns3_url[0]).hostname

    # récupère la topologie GNS3, les routeurs etc...
    routers, gs, project_id, liens = get_gns_conf(vals.gns3_url[0],vals.gns3_password[0])

    if vals.show_topology:
        show_topology(routers)
        exit(0)

    if vals.gen_skeleton:
        print(yaml.dump(data=generate_skeleton(list(routers.values()), liens), indent=2, sort_keys=False))
        exit(0)

    user_config = load_user_conf(vals.import_user_conf[0])

    if vals.export_user_conf:
        print(json.dumps(user_config, indent=2, sort_keys=False))
        exit(0)

    # partie des commandes global (-g)
    if len(vals.global_cmd) > 0:
        cmd = " ".join(vals.global_cmd)
        print(f"Exécution de la commande `{cmd}` sur tous les routeurs")
        _c = cmd.encode('ascii', 'ignore')
        print(f"exec {_c}")
        for router in routers.values():
            print(f"Routeur {router.name}")
            console = Console.from_router(router)
            console.write_cmd(b'\r')
            console.write_cmd(_c+b'\r\n')
            time.sleep(0.1)
        exit(0)

    # partie de génération des confs
    all_confs = []
    for router in routers.values():
        jc = resolve_router_config(router)
        text_conf = generate_conf(jc)
        all_confs.append(jc)
        if vals.apply:
            try:
                console = Console(console_host=gns3host,console_port=router.console_port)
                configure_router(router, text_conf, console)
            except ConnectionRefusedError as e:
                raise e
    if vals.gen_hosts:
        print(gen_hosts_file(all_confs))
        exit(0)
    print("Les fichiers configurations pour les routeurs ont été écrits dans le dossier `./output`")
    if not vals.apply:
        print("Si vous désirez envoyer automatiquement les configurations aux routeur, relancez"
              " ce programme avec --apply")
    # partie de génération des jolis dessins
    project = gns3fy.Project(project_id=project_id, connector=gs)
    project.get()
    delete_drawings(project)
    if vals.delete_labels:
        exit(0)
    if vals.hide_labels:  # oui c'est bizarre c'est inversé
        display_tracked_subnets(project, liens)
        display_router_ids(project, routers)
        display_costs(project, routers)
