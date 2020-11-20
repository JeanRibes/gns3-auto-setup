import time

import gns3fy

from config import *
from util import *


def make_config(router: Node, area: str = OSPF_AREA, ospf_process: int = OSPF_PROCESS) -> str:
    s = main_menu
    s += f"""#--
{get_extra_global_conf(router.name)}
end
conf t
"""
    if get_is_router_disabled(router.name):
        return "# configuration automatique desactivee par l'utilisateur"
    rid = get_router_id_overriden(router.name)
    if rid:
        router.router_id = rid
    s += f"""###### config pour {router.name} ######
ipv6 unicast-routing
ipv6 cef
ip cef
ipv6 router ospf {ospf_process}
    redistribute connected
    router-id {router.router_id}
  exit
router ospf {ospf_process}
    redistribute connected subnets
    router-id {router.router_id}
  exit
#--
"""

    for interface in router.interfaces:
        extra_conf_int = get_extra_interface_conf(router.name, interface.get_name())
        if len(extra_conf_int) > 1:
            s += f"""#--
int {interface.get_name()}
{extra_conf_int}
end
conf terminal
"""
        if get_is_interface_disabled(router.name, interface.get_name()):
            continue
        s += f"""#--
int {interface.get_name()}
    description connexion a l'interface {interface.reverse_int()} du routeur {interface.reverse_router().name}
    no shut
    ipv6 enable
    mpls ip
    ipv6 address {interface.get_ip6()}
    ip address {interface.get_ip4()}
    """
        if interface.reverse_router().router:
            s += f"ipv6 ospf {ospf_process} area {area}\n"
            s += f"ip ospf 1 area 0\n"

    s += f"""
end
###### fin de la config pour {router.name} ######
"""

    return s


def apply_config(router: Node, config: str):
    console = Console(router.console_host, router.console)

    console.write_cmd(b'\r')  # active la console
    console.write_cmd(b'end')
    console.write_cmd(b'configure terminal')
    for part in config.split('#--'):
        console.write_conf(part)
        time.sleep(0.1)


if __name__ == '__main__':
    gs = gns3fy.Gns3Connector("http://localhost:3080", user="admin")
    if GNS3_PROJECT_NAME != 'auto':
        project_id = gs.get_project(name=GNS3_PROJECT_NAME)['project_id']
    else:
        # sinon on récup le 1er projet ouvert dans GNS3 en ce moment
        project_id = list(filter(lambda p: p['status'] == 'opened', gs.get_projects()))[0]['project_id']
    project = gns3fy.Project(project_id=project_id, connector=gs)
    project.get()

    # énumération des noeuds du projet et initialisation des consoles
    mynodes = enumerate_nodes(gs, project_id)

    # énumération & résolution des liens puis assignation des réseaux
    liens = enumerate_links(gs, project_id, mynodes)

    # print(make_config(mynodes.get_by_name('R5')))
    # exit(0)

    # applique les configs sur tous les routeurs
    for node in mynodes.values():
        if node.router:
            cfg = make_config(node)  # génère la config
            # print(cfg)
            print(f"envoi de la configuration à {node.name} (router-id {node.router_id}) ... ", end="")
            apply_config(node, cfg)  # reconfigure le routeur Cisco
            print("fini !")

    # efface les dessins précédents
    project.get_drawings()
    delete_drawings(project)

    # partie qui fait le joli affichage dans GNS3
    # il faut qu'elle soit après la génération des configs car certaines valeurs 'custom' sont récupérées à ce moment
    display_subnets(project, liens)
    display_router_ids(project, mynodes.values())
