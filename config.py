# tapez "menu m" dans le shell IOS
main_menu = """
menu ospf command 1 show ipv6 ospf interface brief
menu ospf command 2 show ipv6 ospf neighbor
menu ospf command 3 sh ipv6 route ospf | include OE2
menu ospf command 4 show ipv6 ospf database

menu bgp command 1 show ip bgp
menu bgp command 2 show bgp ipv6 unicast summary
menu bgp command 
menu bgp command 

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

default_yaml = '---\ndefault_router_classes:\n  - ospf6-router\n  - ospf4-router\n  - bgp-router\ndefault_interface_classes: [ ]\nclasses:\n  - name: ospf6-router\n    type: router\n    template: |-\n      ipv6 router ospf {{router.ospf6_process}}\n        redistribute connected\n        router-id {{router.router_id}}\n      exit\n    interface_classes:\n      - ospf6-interface\n    values:\n      ospf6_process: 1\n      ospf6_area: 0\n  - name: ospf4-interface\n    type: interface\n    template: |-\n      ip ospf {{router.ospf4_process}} area {{router.ospf4_area}}\n  - name: ospf4-router\n    type: router\n    template: |-\n      router ospf {{router.ospf4_process}}\n        router-id {{router.router_id}}\n        redistribute connected subnets\n      exit\n    values:\n      ospf4_process: 4\n      ospf4_area: 0\n    interface_classes:\n      - ospf4-interface\n    classes:\n      - mpls-router\n  - name: ospf6-interface\n    type: interface\n    template: ipv6 ospf {{router.ospf6_process}} area {{router.ospf6_area}}\n\n  - name: mpls-interface\n    type: interface\n    template: mpls ip\n\n  - name: mpls-router\n    type: router\n    template: |-\n      ip cef\n      ipv6 cef\n    interface_classes:\n      - mpls-interface\n  - name: bgp-router\n    type: router\n    template: |-\n      router bgp {{router.asn}}\n          bgp router-id {{router.router_id}}\n      {% for interface in router.interfaces %}\n        {% if interface.peer %}\n          neighbor {{interface.peer.ipv4}} remote-as {{interface.peer.asn}}\n          neighbor {{interface.peer.ipv4}} activate\n        {% endif %}\n      {% endfor %}\n\n          address-family ipv6 unicast\n      {% for interface in router.interfaces %}\n        {% if interface.peer %}\n              neighbor {{interface.peer.ipv6}} remote-as {{interface.peer.asn}}\n              neighbor {{interface.peer.ipv6}} activate\n        {% endif %}\n      {% endfor %}\n            redistribute connected\n          exit-address-family\n\n          address-family ipv4 unicast\n              redistribute connected\n          exit-address-family\n      exit\n  - name: ospf6-cost\n    type: interface\n    template: ipv6 ospf cost {{interface.ospf6_cost}}\nlinks:\n  - name: R1<-->R3 #ça marche dans les deux sens\n    interface_classes: [ ]\n    router_classes: [ ]\n    template: "# oh que oui {{interface.oui}}"\n    interface_values:\n      oui: oh non\nrouters:\n  - name: R1\n    disable: false\n    classes: [mpls-router,]\n    template: ""\n    interfaces:\n      - name: f0/0\n        classes: [mpls-interface,]\n        template: no ipv6 ospf 1 area 1\n        values:\n          ip_end6: \'101\'\n\n      - name: f5/0\n        disable: false\n        classes:\n          - ospf6-cost\n        values:\n          ospf6_cost: 5\n\n      - name: f1/0\n        template: \'\'\n        values:\n          ipv6_network: \'2001:1:1:1\'\n          ip_end: \'1\'\n          ipv6_prefixlen: 64\n          ipv4_network: 192.168.0.0\n          ipv4_netmask: 255.255.255.0\n\n    values:\n      router_id: 10.0.0.10\n\n  - name: R2\n    disable: true\n    template: |-\n      router rip\n        redistribute connected\n      exit\ntemplates:\n  router: |-\n    #### configuration de {{router.name}}\n    ipv6 unicast-routing\n    no ip domain lookup\n\n    {% for interface in router.interfaces %}\n    {{Template(interface.template).render(Template=Template,interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n    #--\n    {% endfor %}\n\n    # les templates provenant des classes seront remplaces a la 2e passe de templating\n    {% for classe in router.resolved_classes %}\n    # classe {{classe.name}}\n    {{Template(classe.template).render(Template=Template,classe=classe,router=router,construct_ipv4=construct_ipv4)}}\n    #--\n    # fin classe {{classe.name}}\n    {% endfor %}\n\n    {% if router.disable %}# ce routeur ne doit pas etre configure{% endif %}\n\n    # template specifique\n    {{Template(router.router_template).render(Template=Template,router=router,construct_ipv4=construct_ipv4)}}\n    #fin de la configuration de {{router.name}}\n\n\n  interface: |2-\n\n    interface {{interface.name}}\n    {% if interface.disable %}\n    # cette interface ne doit pas etre configuree\n    {% endif %}\n    {% if interface.peer %}\n      description connectee a {{interface.peer.interface}} de  {{interface.peer.name}}\n    {% endif %}\n      no shutdown\n      ipv6 enable\n      ipv6 address {{interface.ipv6_network}}::{{interface.ip_end}}/{{interface.ipv6_prefixlen}}\n      ip address {{construct_ipv4(interface.ipv4_network,interface.ip_end)}} {{interface.ipv4_netmask}}\n      {% for classe in interface.resolved_classes %}# classe {{classe.name}}\n        {{Template(classe.template).render(interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n        # fin classe {{classe.name}}\n      {% endfor %}\n      #template specifique a cette interface\n        {{ interface.interface_template }}\n    exit\n    # fin interface {{interface.name}}'