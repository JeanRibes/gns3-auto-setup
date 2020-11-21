GNS3_PROJECT_NAME = "auto"  # le nom de votre projet. "auto" utilise celui qui est ouvert
OSPF_AREA = '0'
OSPF_PROCESS = 1

config_custom = {  # permet de rajouter des paramètres personalisés et les templates
    'templates': {  # définit les templates de base appliqués à tous les routeurs
        'router':  # template pour un routeur, requis
            """#### configuration de {{router.name}}
            ipv6 unicast-routing
            
            # rendered_interfaces contient la configuration des interfaces, déjà générée
            {% for interface in rendered_interfaces %}
            {{interface}}
            {% endfor %}
            
            # les templates provenant des classes seront remplacés à la 2e passe de templating
            {% for classe in router.resolved_classes %}
            # classe {{classe.name}}
            {{classe.template}}
            # fin classe {{classe.name}}
            {% endfor %}
            
            {% if router.disable %}# ce routeur ne doit pas être configuré{% endif %}
            # fin de la configuration de {{router.name}}
            """,  #
        #
        'interface':  # requis
            """interface {{interface.name}}
                {% if interface.disable %}# cette interface ne doit pas être configuré{% endif %}
                no shutdown
                ipv6 enable
                ipv6 address {{interface.ip_network6}}::{{interface.ip_end6}}/64
            {% for classe in interface.resolved_classes %}
            {{classe.template}}
            {% endfor %}
            {{ interface_template }}
            exit
            # fin interface {{interface.name}}"""

    },
    'default_router_classes': ['ospf6-router'],  # des classes qui seront appliquées à tous les routeurs
    'default_interface_classes': [],
    # on peut assigner une classe à des routeurs, interfaces ou même liens
    'classes': [
        {
            'name': 'ospf6-router',
            'type': 'router',  # on ne peut pas appliquer une classe à un routeur ET une interface
            'template': """ipv6 router ospf {{ospf_process}}
    redistribute connected
    router-id {{router.router_id}}
  exit""",
            'interface_classes': ['ospf6-interface'],  # les interfaces de ce routeur auront ces classes
            'values': {
                'ospf_process': 1,
                'ospf_area': 0,
            }
        },
        {
            'name': 'ospf6-interface',
            'type': 'interface',
            'template': "    ipv6 ospf {{router.ospf_process}} area {{router.ospf_area}}"
        },
    ],
    'links':
        [
            {
                'name': 'R1<-->R3',
                'interface_classes': [],
                'router_classes': [],
                'template': '# oh que oui'
            }
        ],
    'routers': {
        'R1': {
            'classes': ['ospf6-router'],
            'template': 'no ip router ospf\n',
            'interfaces': {
                'f0/0': {
                    'classes': [],
                    'template': 'no ipv6 ospf 1 area 1',
                    'values': {
                        'ip_end6': '101',
                    }
                },
                'f5/0': {'disable': True},
                # 'f2/0': {'disable': True},
                'f1/0': {
                    'template':'# specifique',
                    'values': {
                        'ip_network6': '2001:1:1:1',
                        'ip_end6': '1',
                    }
                },
            },
            'values': {
                'router_id': '10.0.0.10',
            }
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
            'disable': True,
            'template': 'router ospf 1\n  router-id {{router_id}}',
        },
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
