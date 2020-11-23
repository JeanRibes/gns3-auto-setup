GNS3_PROJECT_NAME = "auto"  # le nom de votre projet. "auto" utilise celui qui est ouvert

# changez dans ce fichier les configurations.
# les templates par defaut sont

default_router_template = """#### configuration de {{router.name}}
ipv6 unicast-routing
            
{% for interface in router.interfaces %}
{{Template(interface.template).render(Template=Template,interface=interface,router=router,construct_ipv4=construct_ipv4)}}
#--
{% endfor %}
            
# les templates provenant des classes seront remplaces a la 2e passe de templating
{% for classe in router.resolved_classes %}
# classe {{classe.name}}
{{Template(classe.template).render(Template=Template,classe=classe,router=router,construct_ipv4=construct_ipv4)}}
#--
# fin classe {{classe.name}}
!
{% endfor %}
            
{% if router.disable %}# ce routeur ne doit pas etre configure{% endif %}
# template specifique
{{Template(router.router_template).render(Template=Template,router=router,construct_ipv4=construct_ipv4)}}
# fin de la configuration de {{router.name}}
"""

default_interface_template = """
interface {{interface.name}}
{% if interface.disable %}
# cette interface ne doit pas etre configuree
{% endif %}
{% if interface.peer %}
    description connectee a {{interface.peer.interface}} de  {{interface.peer.name}}
{% endif %}
    no shutdown
    ipv6 enable
    ipv6 address {{interface.ipv6_network}}::{{interface.ip_end}}/{{interface.ipv6_prefixlen}}
    ip address {{construct_ipv4(interface.ipv4_network,interface.ip_end)}} {{interface.ipv4_netmask}}
    {% for classe in interface.resolved_classes %}
# classe {{classe.name}}
    {{Template(classe.template).render(interface=interface,router=router,construct_ipv4=construct_ipv4)}}
# fin classe {{classe.name}}
{% endfor %}
#template specifique a cette interface
    {{ interface.interface_template }}
  exit
# fin interface {{interface.name}}"""


config_custom = {  # permet de rajouter des parametres personalises et les templates
    'templates': {  # definit les templates de base appliques a tous les routeurs
        'router': default_router_template,  # template pour un routeur, requis
        'interface': default_interface_template  # requis
    },
    'default_router_classes': ['ospf6-router', 'ospf4-router', 'bgp-router'],
    # des classes qui seront appliquees a tous les routeurs
    'default_interface_classes': [],
    # on peut assigner une classe a des routeurs, interfaces ou meme liens
    'classes': [
        {
            'name': 'ospf6-router',
            'type': 'router',  # on ne peut pas appliquer une classe a un routeur ET une interface
            'template': """ipv6 router ospf {{router.ospf6_process}}
    redistribute connected
    router-id {{router.router_id}}
  exit""",
            'interface_classes': ['ospf6-interface'],  # les interfaces de ce routeur auront ces classes
            'values': {
                'ospf6_process': 1,
                'ospf6_area': 0,
            }
        },
        {
            'name': 'ospf4-interface',
            'type': 'interface',
            'template': """ip ospf {{router.ospf4_process}} area {{router.ospf4_area}}
            """
        },
        {
            'name': 'ospf4-router',
            'type': 'router',
            'template': """router ospf {{router.ospf4_process}}
            router-id {{router.router_id}}
            redistribute connected subnets
            exit""",
            'values': {
                'ospf4_process': 2,
                'ospf4_area': 0,
            },
            'interface_classes': ['ospf4-interface'],
            'classes': ['mpls-router']
        },
        {
            'name': 'ospf6-interface',
            'type': 'interface',
            'template': "ipv6 ospf {{router.ospf6_process}} area {{router.ospf6_area}}",
        },
        {
            'name': 'mpls-interface',
            'type': 'interface',
            'template': 'mpls ip'
        },
        {
            'name': 'mpls-router',
            'type': 'router',
            'template': 'ip cef\nipv6 cef',
            'interface_classes': ['mpls-interface']
        },
        {
            'name': 'bgp-router',
            'type': 'router',
            'template': """
router bgp {{router.asn}}
    bgp router-id {{router.router_id}}
    {% for interface in router.interfaces %}{% if interface.peer %}
    neighbor {{interface.peer.ipv4}} remote-as {{interface.peer.asn}}
    address-family ipv6 unicast
        neighbor {{interface.peer.ipv6}} remote-as {{interface.peer.asn}}
        neighbor {{interface.peer.ipv6}} activate
    exit-address-family
    neighbor {{interface.peer.ipv4}} activate
    {% endif %}{% endfor %}
    address-family ipv4 unicast
        redistribute connected
    exit-address-family
    address-family ipv6 unicast
        redistribute connected
    exit-address-family
exit
!""",
            'values': {
                'announce_internal': True,
            }
        },
        {
            'name': 'ospf6-cost',
            'type': 'interface',
            # attention il faudra definie cette variable dans les 'values' des interfaces de chque routeur sur lequel on l'active
            'template': 'ipv6 ospf cost {{interface.ospf6_cost}}'
        }
    ],
    'links':
        [
            {
                'name': 'R1<-->R3',
                'interface_classes': [],
                'router_classes': [],
                'template': '# oh que oui {{interface.oui}}',
                'interface_values': {
                    'oui': 'oh non'
                }
            }
        ],
    'routers': {
        'R1': {
            'disable': False,
            'classes': [],
            'template': '#RR11\nrouter ospf {{router.ospf4_process}}\n network 192.168.0.0 255.255.255.0 area {{router.ospf4_area}}\nexit',
            'interfaces': {
                'f0/0': {
                    'classes': [],
                    'template': 'no ipv6 ospf 1 area 1',
                    'values': {
                        'ip_end6': '101',
                    }
                },
                'f5/0': {
                    'disable': False,
                    'classes': ['ospf6-cost'],
                    'values': {
                        'ospf6_cost': 5,
                    }
                },
                # 'f2/0': {'disable': True},
                'f1/0': {
                    'template': '',
                    'values': {
                        'ipv6_network': '2001:1:1:1',
                        'ip_end': '1',
                        'ipv6_prefixlen': 64,
                        'ipv4_network': '192.168.0.0',
                        'ipv4_netmask': '255.255.255.0',
                    }
                },
            },
            'values': {
                'router_id': '10.0.0.10',
            }
        },
        'R2': {
            'disable': True,
            'template': 'router ospf 1\n  router-id {{router_id}}',
        },
        'R3': {
            'interfaces': {
                'f3/0': {
                    'classes': ['ospf6-cost'],
                    'values': {
                        'ospf6_cost': 10,
                    }
                }
            }
        }
    }
}

# tapez "menu m" dans le shell IOS
main_menu = """
menu ospf command 1 show ipv6 ospf interface brief
menu ospf command 2 show ipv6 ospf neighbor
menu ospf command 3 sh ipv6 route ospf | include OE2
menu ospf command 4 show ipv6 ospf database
menu ospf command 5 

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
