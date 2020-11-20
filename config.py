GNS3_PROJECT_NAME = "auto"  # le nom de votre projet. "auto" utilise celui qui est ouvert
OSPF_AREA = '0'
OSPF_PROCESS = 1

config_custom = {  # permet de rajouter des paramètres personalisés et les templates
    # on peut assigner une classe à des routeurs, interfaces ou même liens
    'classes': [
        {
            'name': 'routeur-coeur',
            'template': 'router bgp {{router_id}}',
            'values': {
                'a': 1,
                'b': 'boii',
            }
        }, {
            'name': 'interface-out',
            'template': 'ip address {{interface.ip4}}'
        },
        {
            'name': 'fibre',
            'template': 'nope',
        }
    ],
    'links':
        [
            {
                'name': 'R1<-->R5',  # on peut aussi marquer 'R5<-->R1'
                'classe': 'fibre',
                'extra_router': """no ipv6 router rip""",
                'extra_interface': '    no shut\n    #hi from extra int link',
                'override_network6': '2001:100:4',
                'override_network4': '192.168.5',
                'disable': False,  # désactive intégralement la configuration de l'interface associée
            },
        ],
    'routers': {
        'R5': {
            'classe': 'routeur-coeur',
            'interfaces': {
                'f0/0': {'extra': '    arp log threshold entries 2'},
                'f3/0': {'disable': True},
                'f2/0': {'disable': True},
                'f1/0': {'disable': True},
            },
            'extra': 'router rip\n   redistribute connected\n  exit'
        },
        'R8': {  # nom (hostname) du routeur. je vais modifier la configuration du routeur R8 ici
            'disable': False,  # désactive la configuration auto de ce routeur
            'router_id_override': '8.8.0.8',  # pour changer les router-id à la main
            'extra': "ipv6 router rip OUI\nredistribute connected",
            # pour rajouter une configuration globale au routeur.
            # mettre '\n' pour les sauts de lignes
            'interfaces': {  # modification de certaines interfaces
                'f2/0':  # attention c'est le nom "GNS3" de l'interface (aussi affiché dans le panneau "Topology Summary" à droite
                    {
                        'disable': False,  # désactive la configuration automatique de cette interface
                        # extra permet de rajouter de la config dans le contexte d'une interface même si la conf auto est désactivée
                        'extra': "ipv6 address 2001:0:8::1/64\nip address 10.8.0.1 255.255.255.0 secondary"
                    },
                'f0/0': {
                    'disable': True,
                    # pour sauter des lignes on peut mettre des '\n' mais aussi passer en mode triple-guillemets (verbatim)
                    'extra': """    no shutdown
  description moi utilisateur, je configure cette interface entierement a la main
  mpls bgp forwarding
  ipv6 address autoconfig"""
                }
            }
        },
        'R2': {
            'disable': True
        }
    }
}

router_template = """
ipv6 unicast-routing
ipv6 cef
ip cef
ipv6 router ospf ${ospf_process}
    redistribute connected
    router-id $router_id
  exit
router ospf ${ospf_process}
    redistribute connected subnets
    router-id ${router_id}
  exit
"""

# template pour toutes les interfaces
interface_base_template = """#--
int ${interface_name}
    description connexion a l'interface ${reverse_interface_name} du routeur ${reverse_router_name}
    no shut
    ip address ${ip4}
    mpls ip
    ipv6 enable
    ipv6 address ${ip6}
"""

# template ajouté aux interface de routages, i.e. connectées à un autre routeur
interface_routing_template = """
    ipv6 ospf ${ospf_process} area ${area}
    ipv ospf ${ospf_process} area ${area}
"""
# tapez "menu m" dans le shell IOS
main_menu = """
menu m command 1 show ipv6 ospf neighbor
menu m command 2 sh ipv6 route ospf | include OE2
menu m command 3 show mpls forwarding-table
menu m command 4 sh ip ospf neighbor
menu m command 5 show ipv6 ospf database
menu m command 6 show ip ospf database
menu m command 7 show arp
menu m command e menu-exit
menu m command q menu-exit
menu m prompt $ ===============Menu d'infos rapide=====================

1. voisins OSPFv6
2. routes externes d'OSPFv6
3. table de forwarding MPLS
4. voisins OSPFv4
5. link-state database OSPFv6
6. link-state database OSPFv4
7. Table ARP

(e|q). revenir a la ligne de commande Cisco IOS. Pour revoir ce menu, tapez `menu m`

------------------------------------
Votre choix: $

"""
