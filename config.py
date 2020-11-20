GNS3_PROJECT_NAME = "auto"  # le nom de votre projet. "auto" utilise celui qui est ouvert
OSPF_AREA = '0'
OSPF_PROCESS = 1

config_custom = {  # permet de rajouter des paramètres personalisés
    'links':
        [
            {
                'name': 'R1<-->R5',  # on peut aussi marquer 'R5<-->R1'
                'extra_router': """no ipv6 router rip""",
                'extra_interface': '    no shut\n    #hi from extra int link',
                'override_network6': '2001:100:4',
                'override_network4': '192.168.5',
                'disable': True,
            },
        ],
    'routers': {
        'R5': {
            'interfaces': {
                'f0/0': {'extra': '    arp log threshold entries 2'},
            },
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
