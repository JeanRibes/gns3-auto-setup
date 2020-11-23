# Autoconfigurateur Cisco IOS
Ce script python se connecte au serveur GNS3 local et configure entièrement 
un réseau OSPF sur tous les routeurs Cisco. Il effectue tout seul l'adressage IP, l'allocation
des ``router-id``... 

Il s'adapte à n'importe quelle topologie réseau, et vous êtes libre de choisir le nom de vos routeurs ! 
Il est possible de personaliser la configuration avec le système de templates et valeurs.
Vous pouvez remplacer tout ce qui est généré par l'autoconfiguration et changer les templates.

Le script génère des configurations Cisco et peut les applique tout seul aux routeurs via la 
console telnet GNS3
![Diagramme GNS3](screenshot.jpg "Diagramme GNS3")

# Table des matières

- [Fonctionnalités](#fonctionnalités)
  * [Autoconfiguration](#autoconfiguration)
  * [Templates dynamiques](#templates-dynamiques)
  * [Abstractions](#abstractions)
  * [Multi-shell](#multi-shell)
- [Installation](#installation)
  * [Avec un virtualenv](#avec-un-virtualenv)
  * [Sans virtualenv](#sans-virtualenv)
  * [Configuration de GNS3](#configuration-de-gns3)
- [Utilisation](#utilisation)
  * [Personaliser des parties de la configuration](#personaliser-des-parties-de-la-configuration)
    + [Comment debug](#comment-debug)
  * [Problèmes](#problèmes)
  * [Limitations](#limitations)
  * [Diagramme dans GNS3](#diagramme-dans-gns3)
    + [Je peux pas bouger les dessins](#je-peux-pas-bouger-les-dessins)
    + [J'arrive plus à cliquer sur les routeurs pour accéder à la console !](#j'arrive-plus---cliquer-sur-les-routeurs-pour-acc-der---la-console--)
  * [TODO](#todo)
  * [Crédits](#crédits)
- [Format de données](#format-de-données)
  * [configuration utilisateur](#configuration-utilisateur)
  * [représentation interne disponible dans les templates](#représentation-interne-disponible-dans-les-templates)
  * [Configuration résultant de ces données:](#configuration-résultant-de-ces-données-)



# Fonctionnalités

## Autoconfiguration
Ce script récupère la topologie de votre réseau et crée tout seul un plan d'allocation d'adresses IP
pour les liens entre routeurs. Il alloue les Router-ID et les ASN.

## Templates dynamiques
Des templates extensibles et dynamique mélangent les données d'autoconfiguration avec 
la configuration utilisateur pour générer une configuration Cisco IOS.

Les templates de base déploient un réseau OSPF/BGP/mpls d'exemple en IPv6 & IPv4.

Chaque élément (**routeur**, **interface**, **lien**) peut définir des **values** et des **templates** qui seront
mixés dans la configuration finale. Les *values* seront insérées dans la représentation interne des données de configuration et donc accessibles dans tous les templates.
Cela permet une organisation flexible et puissante.

## Abstractions
Les **classes** vous permettent de changer la configuration des différents routeurs sans dupliquer les éléments de configuration.
Une classe peut référencer d'autres classes de manière récursive, ce qui vous permet de définir des groupes de routeurs et des morceaux de configurations que l'on peut ou pas ajouter.

Vous pourriez par exemple avoir une classe qui configure le coût d'un lien OSPF et ensuite
définir sur chaque interface de chaque routeur le coût choisi. Mais vous pouvez également faire une 
nouvelle classe qui définit la valeur du coût et appliquer cette classe à plusieurs interfaces ou même
à toutes les interfaces d'un routeur.

## Multi-shell
Avec ``python3 main.py -g ``, vous pouvez exécuter une commande sur tous les routeurs Cisco. Ça peut vous économiser du temps.


# Installation
## Avec un virtualenv
```
git clone https://github.com/JeanRibes/gns3-auto-setup.git gns3-auto-setup
cd gns3-auto-setup
python3 -m venv venv
virtualenv -p /usr/bin/python3 venv
source venv/bin/activate # vous devez tapez cette ligne à chaque fois que vous ré-ouvez un terminal dans le dossier gns3-auto-setup 
# s'il n'y a pas (venv) au début de votre ligne de commande il faut installer python3-venv ou virtualenv
pip3 install gns3fy==0.7.1 Jinja2==2.11.2
```
## Sans virtualenv
```
git clone https://github.com/JeanRibes/gns3-auto-setup.git gns3-auto-setup
cd gns3-auto-setup
pip3 install --user gns3fy==0.7.1 Jinja2==2.11.2
```
## Configuration de GNS3

* créez un nouveau projet vide dans GNS3
* allez dans *Edit > Preferences > Server > Main Server*
* décochez `protect server with password`
* faites *Ok*

# Utilisation
* Ouvrez votre projet
* Lancez votre projet (si c'est déjà pas besoin de relancer)
* Attendez que les routeurs démarrent
* Lancez le script
* Attendez que les routeurs se découvrent et propagent leurs routes
Et vous avez votre réseau OSPF, BGP, mpls sans effort !

```
usage: main.py [-h] [--gen-skeleton] [--hide-labels] [--delete-labels] [--apply] [--show-topology] [--global-cmd commande [commande ...]] [--export-user-conf] [--import-user-conf user-conf.yaml]

Configurateur automatique de routeurs dans GNS3

optional arguments:
  -h, --help            show this help message and exit
  --gen-skeleton        Affiche un squelette de configuration adapté au réseau détécté, sans configurer les routeurs.
  --hide-labels, -n     Crée des jolis labels dans GNS3 pour afficher les subnets, router-id et ASN
  --delete-labels       Efface tous les labels crées par ce programme de GNS3 puis termine.
  --apply, -a           Active l'envoi automatique des configurations aux routeurs
  --show-topology       Montre la topologie détéctée par ce script.
  --global-cmd commande [commande ...], -g commande [commande ...]
                        Une commande qui sera exécutée sur tous les routeurs en même temps. Pas besoin d'utiliser de guillemets
  --export-user-conf, -e
                        Exporte la configuration utilisateur au format JSON et termine
  --import-user-conf user-conf.yaml, -i user-conf.yaml
                        Utilise la configuration utilisateur depuis un fichier YAML
```
## Personaliser des parties de la configuration
Le fichier `user-conf.yaml` vous permet de rajouter votre grain de sel. Regardez les configurations générées
et les données JSON pour savoir comment modifier les templates.


Le langage de template utilisé est *Jinja2*, qui a la même syntaxe que les templates *Django*.
Attention, pour faire le rendu d'un template dans un autre, il faut faire comme suit:
```jinja2
{{Template(child.template).render(Template=Template,construct_ipv4=construct_ipv4,parent=parent,child=child)}}
```
Il faut passer la classe ``Template`` en variable pour que les templates enfants puissent marcher. La fonction `construct_ipv4` permet de générer une adresse IPv4 à partir d'un réseau et du numéro de la machine
La configuration d'exemple fait cela pour les *interfaces* et les *classes*.

Pour trouver les noms des interfaces, activez dans GNS3 *View > Show/Hide interfaces labels*

### Comment debug
Le script place les configurations qu'il a générées dans un sous-dossier ``output`` du dossier courant.
Vous trouverez dedans la configuration Cisco mais aussi un fichier *json* qui contient toutes les données utilisées
pour générer la configuration. Ça peut vous être utile pour personaliser les templates.

Pour éditer le fichier YAML, si vous utilisez un IDE Jetbrains, vous pouvez ajouter le JSON-Schema pour faire la validation.
## Problèmes
L'allocation des **ASN**, des **router-id** et des **subnets IPv4** n'est pas déterministe et peut changer entre
si vous rajoutez des routeurs. Je vous recommande donc de ne pas faire de ``write`` sur les routeurs
et de les redémarrer quand vous rajoutez/enlevez des routeurs.

Sinon il est aussi possible de rajouter une 'anti-configuration' qui désactive tout juste avant la nouvelle configuration. 

## Limitations
* Les templates par défaut ne font rien des clés `'disable'`, mais vous pouvez en choisir le fonctionnement
  avec ``{% if router.disable %}...{% endif %}``.

* Si vous modifiez les adresses des interfaces, le diagramme dans GNS3 ne reflètera pas vos modifications.

  ça peut se résoudre en modifiant les fonctions de dessin (pour qu'elles utilisent le dictionnaire renvoyé par `resolve_router_config()`

* le script efface les sauts de lignes superflus pour réduire la taille des confs Cisco
  pour avoir un saut de ligne (ligne vide), soit vous changez le fonctionnement soit vous faites
  comme Cisco dans ``show running-config``, mettez un point d'exclamation `!` sur la ligne.

* Si vous modifiez l'adresse IP par défaut, ces modifications ne sont pas reflétées dans ``interface.peer`` (embêtant pour BGP)
## Diagramme dans GNS3
Ce script crée automatiquement des petites étiquettes/dessins dans GNS3 pour afficher le
sous-réseau actif sur un lien (IPv4 et IPv6).
Il affiche aussi le router-id et l'ASN par dessus l'icône du routeur.

### Je peux pas bouger les dessins
C'est normal, ils sont verrouillées pour que le script les retrouve et puisse les supprimer.
Si vous voulez tous les enlever, relancez le script avec `--delete-labels`. Pour les bouger il suffit de faire clic droit > *Unlock item*.

Mais si vous faites ça il faudra les supprimer à la main.

### J'arrive plus à cliquer sur les routeurs pour accéder à la console !
Utilisez le bouton *Control > Console connect to all nodes*

Si c'est trop agaçant vous pouvez utiliser le programme avec ``--hide-labels`` pour ne pas créer les dessins la prochaine fois.


## TODO
 * [ ] pouvoir tagger les routeurs & interfaces en groupes
 * [x] faire en sorte que l'utilisateur fournisse les templates (jinja2 ? pug ?)
 * [x] pouvoir assigner des coûts aux liens pour du Traffic engineering (et les afficher avec des dessins GNS3)
 * [ ] configurer les conteneurs Docker
 * [ ] avoir un GUI ? (mdr)
 * [x] option pour générer juste un squelette des configs ?
 * [x] générer des adresses IPv4 qui font des réseaux en /30 pour être + économe
 * [x] séparer le réseau et l'adresse dans le JSON pour pouvoir configurer facilement BGP
avoir comme clés ip_network, ip_end, ip_mask et ip_prefixlen, toutes configurables & en ipv4 et v6
* [ ] avoir un template par défaut pour les ``edge devices`` et les rajouter dans la représentation interne
* [ ] avoir des templates par défaut pou FRRrouting & Quagga

### Pistes pour une interfaces graphique
Rapide et stylé: un éditer JSON-schema: [json-editor](https://json-editor.github.io/json-editor/) et on génère le schéma
ave [jsonchema.net](https://jsonschema.net/home)
----
> est-ce que j'ai gagné du temps en automatisant mon travail ? c'est pas sûr

### Crédits
 * Le package [gns3fy](https://github.com/davidban77/gns3fy) de David Flores
 * Helm pour l'inspiration des templates/values et le YAML
# Format de données

Les données de configuration (la représentation interne) apparaissent dans le dossier `ouput` au format JSON.
La configuration utilisateur est définie dans la (grosse) variable ``custom_config`` du fichier ``config.py.``

La commande ``python3 main.py --gen-skeleton`` vous crée un squelette vide de configuration personalisée
que vous pouvez remplir là où vous en avez besoin.

## configuration utilisateur
```python
custom_config = {
    'templates': {
        'router': "",
        'interface': "",
    },
    'default_router_classes': [], # appliqué à tous les routeurs
    'default_interface_classes': [],
    'classes': [{
        'name': "<default>",
        'type': "<router|interface>",
        'template': "",
        'values': {
            'a': 'b',
        },
        'classes':[], # inclusion récursive
        'interface_classes': [], # si la classe est appliquée à un routeur, les interfaces de routeur se verront appliquer ces classes
        
    }],
    'links': [

        {
            'name': "",
            'interface_classes': [], # ces clases seront appliquées aux interfaces de ce lien (sur chaque routeur)
            'router_classes': [], # celles-ci seront appliquées aux routeurs des deux bouts du lien
            'template': "",
            'interface_values': {},
        }],
    'routers': { # notez que c'est bien un dict() et pas une liste !
        "name":{
            'disable': False,
            'classes': [],
            'template': "",
            'interfaces': { # c'est toujours pas une liste !
                "name":{
                    'template': "",
                    'classes': [],
                    'values': {},
                }
            },
            'values': {},
        }}
}

```

## représentation interne disponible dans les templates
```json
 {
    "announce_internal": true,
    "asn": 101,
    "disable": false,
    "interface_classes": [
        "ospf6-interface",
        "mpls-interface",
        "ospf4-interface"
    ],
    "interfaces": [
        {
            "disable": false,
            "interface_template": "# oh que oui {{interface.oui}}",
            "ip_end": 2,
            "ipv4_netmask": "255.255.255.252",
            "ipv4_network": "172.30.128.0",
            "ipv4_prefixlen": 30,
            "ipv6_network": "2001:b399",
            "ipv6_prefixlen": 64,
            "lien": "R3<-->R1",
            "name": "f5/0",
            "ospf6_cost": 5,
            "oui": "oh non",
            "peer": {
                "asn": 102,
                "interface": "f4/0",
                "ipv4": "172.30.128.1",
                "ipv6": "2001:b399::1",
                "name": "R3"
            },
            "resolved_classes": [
                {
                    "name": "mpls-interface",
                    "template": "mpls ip",
                    "type": "interface"
                },
                {
                    "name": "ospf6-cost",
                    "template": "ipv6 ospf cost {{interface.ospf6_cost}}",
                    "type": "interface"
                },
                {
                    "name": "ospf6-interface",
                    "template": "ipv6 ospf {{router.ospf6_process}} area {{router.ospf6_area}}",
                    "type": "interface"
                },
                {
                    "name": "ospf4-interface",
                    "template": "ip ospf {{router.ospf4_process}} area {{router.ospf4_area}}\n            ",
                    "type": "interface"
                }
            ],
            "template": "\ninterface {{interface.name}}\n{% if interface.disable %}\n# cette interface ne doit pas etre configuree\n{% endif %}\n{% if interface.peer %}\n    description connectee a {{interface.peer.interface}} de  {{interface.peer.name}}\n{% endif %}\n    no shutdown\n    ipv6 enable\n    ipv6 address {{interface.ipv6_network}}::{{interface.ip_end}}/{{interface.ipv6_prefixlen}}\n    ip address {{construct_ipv4(interface.ipv4_network,interface.ip_end)}} {{interface.ipv4_netmask}}\n    {% for classe in interface.resolved_classes %}\n# classe {{classe.name}}\n    {{Template(classe.template).render(interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n# fin classe {{classe.name}}\n{% endfor %}\n#template specifique a cette interface\n    {{ interface.interface_template }}\n  exit\n# fin interface {{interface.name}}",
            "uid": "2570445c-69f9-4316-b399-3f034077bd04"
        },
        {
            "disable": false,
            "interface_template": "",
            "ip_end": "1",
            "ipv4_netmask": "255.255.255.0",
            "ipv4_network": "192.168.0.0",
            "ipv6_network": "2001:1:1:1",
            "ipv6_prefixlen": 64,
            "lien": "edge",
            "name": "f1/0",
            "resolved_classes": [],
            "template": "\ninterface {{interface.name}}\n{% if interface.disable %}\n# cette interface ne doit pas etre configuree\n{% endif %}\n{% if interface.peer %}\n    description connectee a {{interface.peer.interface}} de  {{interface.peer.name}}\n{% endif %}\n    no shutdown\n    ipv6 enable\n    ipv6 address {{interface.ipv6_network}}::{{interface.ip_end}}/{{interface.ipv6_prefixlen}}\n    ip address {{construct_ipv4(interface.ipv4_network,interface.ip_end)}} {{interface.ipv4_netmask}}\n    {% for classe in interface.resolved_classes %}\n# classe {{classe.name}}\n    {{Template(classe.template).render(interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n# fin classe {{classe.name}}\n{% endfor %}\n#template specifique a cette interface\n    {{ interface.interface_template }}\n  exit\n# fin interface {{interface.name}}"
        },
        {
            "disable": false,
            "interface_template": "",
            "ip_end": 1,
            "ipv4_netmask": "255.255.255.252",
            "ipv4_network": "172.30.128.12",
            "ipv4_prefixlen": 30,
            "ipv6_network": "2001:b6c1",
            "ipv6_prefixlen": 64,
            "lien": "R1<-->R2",
            "name": "f3/0",
            "peer": {
                "asn": 104,
                "interface": "f0/0",
                "ipv4": "172.30.128.14",
                "ipv6": "2001:b6c1::2",
                "name": "R2"
            },
            "resolved_classes": [
                {
                    "name": "mpls-interface",
                    "template": "mpls ip",
                    "type": "interface"
                },
                {
                    "name": "ospf6-interface",
                    "template": "ipv6 ospf {{router.ospf6_process}} area {{router.ospf6_area}}",
                    "type": "interface"
                },
                {
                    "name": "ospf4-interface",
                    "template": "ip ospf {{router.ospf4_process}} area {{router.ospf4_area}}\n            ",
                    "type": "interface"
                }
            ],
            "template": "\ninterface {{interface.name}}\n{% if interface.disable %}\n# cette interface ne doit pas etre configuree\n{% endif %}\n{% if interface.peer %}\n    description connectee a {{interface.peer.interface}} de  {{interface.peer.name}}\n{% endif %}\n    no shutdown\n    ipv6 enable\n    ipv6 address {{interface.ipv6_network}}::{{interface.ip_end}}/{{interface.ipv6_prefixlen}}\n    ip address {{construct_ipv4(interface.ipv4_network,interface.ip_end)}} {{interface.ipv4_netmask}}\n    {% for classe in interface.resolved_classes %}\n# classe {{classe.name}}\n    {{Template(classe.template).render(interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n# fin classe {{classe.name}}\n{% endfor %}\n#template specifique a cette interface\n    {{ interface.interface_template }}\n  exit\n# fin interface {{interface.name}}",
            "uid": "dd68b3b3-1f11-4ff9-b6c1-25d38c6dd414"
        },
        {
            "disable": false,
            "interface_template": "",
            "ip_end": 1,
            "ipv4_netmask": "255.255.255.252",
            "ipv4_network": "172.30.128.16",
            "ipv4_prefixlen": 30,
            "ipv6_network": "2001:acf4",
            "ipv6_prefixlen": 64,
            "lien": "R1<-->R6",
            "name": "f4/0",
            "peer": {
                "asn": 103,
                "interface": "f2/0",
                "ipv4": "172.30.128.18",
                "ipv6": "2001:acf4::2",
                "name": "R6"
            },
            "resolved_classes": [
                {
                    "name": "mpls-interface",
                    "template": "mpls ip",
                    "type": "interface"
                },
                {
                    "name": "ospf6-interface",
                    "template": "ipv6 ospf {{router.ospf6_process}} area {{router.ospf6_area}}",
                    "type": "interface"
                },
                {
                    "name": "ospf4-interface",
                    "template": "ip ospf {{router.ospf4_process}} area {{router.ospf4_area}}\n            ",
                    "type": "interface"
                }
            ],
            "template": "\ninterface {{interface.name}}\n{% if interface.disable %}\n# cette interface ne doit pas etre configuree\n{% endif %}\n{% if interface.peer %}\n    description connectee a {{interface.peer.interface}} de  {{interface.peer.name}}\n{% endif %}\n    no shutdown\n    ipv6 enable\n    ipv6 address {{interface.ipv6_network}}::{{interface.ip_end}}/{{interface.ipv6_prefixlen}}\n    ip address {{construct_ipv4(interface.ipv4_network,interface.ip_end)}} {{interface.ipv4_netmask}}\n    {% for classe in interface.resolved_classes %}\n# classe {{classe.name}}\n    {{Template(classe.template).render(interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n# fin classe {{classe.name}}\n{% endfor %}\n#template specifique a cette interface\n    {{ interface.interface_template }}\n  exit\n# fin interface {{interface.name}}",
            "uid": "bf788c6f-0c22-4da3-acf4-0849e0eeab3d"
        },
        {
            "disable": false,
            "interface_template": "no ipv6 ospf 1 area 1",
            "ip_end": 1,
            "ip_end6": "101",
            "ipv4_netmask": "255.255.255.252",
            "ipv4_network": "172.30.128.20",
            "ipv4_prefixlen": 30,
            "ipv6_network": "2001:a151",
            "ipv6_prefixlen": 64,
            "lien": "R1<-->R4",
            "name": "f0/0",
            "peer": {
                "asn": 105,
                "interface": "f3/0",
                "ipv4": "172.30.128.22",
                "ipv6": "2001:a151::2",
                "name": "R4"
            },
            "resolved_classes": [
                {
                    "name": "mpls-interface",
                    "template": "mpls ip",
                    "type": "interface"
                },
                {
                    "name": "ospf6-interface",
                    "template": "ipv6 ospf {{router.ospf6_process}} area {{router.ospf6_area}}",
                    "type": "interface"
                },
                {
                    "name": "ospf4-interface",
                    "template": "ip ospf {{router.ospf4_process}} area {{router.ospf4_area}}\n            ",
                    "type": "interface"
                }
            ],
            "template": "\ninterface {{interface.name}}\n{% if interface.disable %}\n# cette interface ne doit pas etre configuree\n{% endif %}\n{% if interface.peer %}\n    description connectee a {{interface.peer.interface}} de  {{interface.peer.name}}\n{% endif %}\n    no shutdown\n    ipv6 enable\n    ipv6 address {{interface.ipv6_network}}::{{interface.ip_end}}/{{interface.ipv6_prefixlen}}\n    ip address {{construct_ipv4(interface.ipv4_network,interface.ip_end)}} {{interface.ipv4_netmask}}\n    {% for classe in interface.resolved_classes %}\n# classe {{classe.name}}\n    {{Template(classe.template).render(interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n# fin classe {{classe.name}}\n{% endfor %}\n#template specifique a cette interface\n    {{ interface.interface_template }}\n  exit\n# fin interface {{interface.name}}",
            "uid": "ba76bf13-9e76-4352-a151-79d8e8a27ca3"
        }
    ],
    "name": "R1",
    "ospf4_area": 0,
    "ospf4_process": 2,
    "ospf6_area": 0,
    "ospf6_process": 1,
    "resolved_classes": [
        {
            "interface_classes": [
                "ospf6-interface"
            ],
            "name": "ospf6-router",
            "template": "ipv6 router ospf {{router.ospf6_process}}\n    redistribute connected\n    router-id {{router.router_id}}\n  exit",
            "type": "router",
            "values": {
                "ospf6_area": 0,
                "ospf6_process": 1
            }
        },
        {
            "name": "bgp-router",
            "template": "\nrouter bgp {{router.asn}}\n    bgp router-id {{router.router_id}}\n    {% for interface in router.interfaces %}{% if interface.peer %}\n    neighbor {{interface.peer.ipv4}} remote-as {{interface.peer.asn}}\n    address-family ipv6 unicast\n        neighbor {{interface.peer.ipv6}} remote-as {{interface.peer.asn}}\n        neighbor {{interface.peer.ipv6}} activate\n    exit-address-family\n    neighbor {{interface.peer.ipv4}} activate\n    {% endif %}{% endfor %}\n    address-family ipv4 unicast\n        redistribute connected\n    exit-address-family\n    address-family ipv6 unicast\n        redistribute connected\n    exit-address-family\nexit\n!",
            "type": "router",
            "values": {
                "announce_internal": true
            }
        },
        {
            "interface_classes": [
                "mpls-interface"
            ],
            "name": "mpls-router",
            "template": "ip cef\nipv6 cef",
            "type": "router"
        },
        {
            "interface_classes": [
                "ospf4-interface"
            ],
            "name": "ospf4-router",
            "template": "router ospf {{router.ospf4_process}}\n            router-id {{router.router_id}}\n            redistribute connected subnets\n            exit",
            "type": "router",
            "values": {
                "ospf4_area": 0,
                "ospf4_process": 2
            }
        }
    ],
    "router_id": "10.0.0.10",
    "router_template": "#RR11\nrouter ospf {{router.ospf4_process}}\n network 192.168.0.0 255.255.255.0 area {{router.ospf4_area}}\nexit",
    "template": "#### configuration de {{router.name}}\nipv6 unicast-routing\n            \n{% for interface in router.interfaces %}\n{{Template(interface.template).render(Template=Template,interface=interface,router=router,construct_ipv4=construct_ipv4)}}\n#--\n{% endfor %}\n            \n# les templates provenant des classes seront remplaces a la 2e passe de templating\n{% for classe in router.resolved_classes %}\n# classe {{classe.name}}\n{{Template(classe.template).render(Template=Template,classe=classe,router=router,construct_ipv4=construct_ipv4)}}\n#--\n# fin classe {{classe.name}}\n!\n{% endfor %}\n            \n{% if router.disable %}# ce routeur ne doit pas etre configure{% endif %}\n# template specifique\n{{Template(router.router_template).render(Template=Template,router=router,construct_ipv4=construct_ipv4)}}\n# fin de la configuration de {{router.name}}\n"
}
```

## Configuration résultant de ces données:

```cisco
#### configuration de R1
ipv6 unicast-routing
interface f5/0
    description connectee a f4/0 de  R3
    no shutdown
    ipv6 enable
    ipv6 address 2001:b399::2/64
    ip address 172.30.128.2 255.255.255.252
# classe mpls-interface
    mpls ip
# fin classe mpls-interface
# classe ospf6-cost
    ipv6 ospf cost 5
# fin classe ospf6-cost
# classe ospf6-interface
    ipv6 ospf 1 area 0
# fin classe ospf6-interface
# classe ospf4-interface
    ip ospf 2 area 0
# fin classe ospf4-interface
#template specifique a cette interface
    # oh que oui {{interface.oui}}
  exit
# fin interface f5/0
#--
interface f1/0
    no shutdown
    ipv6 enable
    ipv6 address 2001:1:1:1::1/64
    ip address 192.168.0.1 255.255.255.0
#template specifique a cette interface
  exit
# fin interface f1/0
#--
interface f3/0
    description connectee a f0/0 de  R2
    no shutdown
    ipv6 enable
    ipv6 address 2001:b6c1::1/64
    ip address 172.30.128.13 255.255.255.252
# classe mpls-interface
    mpls ip
# fin classe mpls-interface
# classe ospf6-interface
    ipv6 ospf 1 area 0
# fin classe ospf6-interface
# classe ospf4-interface
    ip ospf 2 area 0
# fin classe ospf4-interface
#template specifique a cette interface
  exit
# fin interface f3/0
#--
interface f4/0
    description connectee a f2/0 de  R6
    no shutdown
    ipv6 enable
    ipv6 address 2001:acf4::1/64
    ip address 172.30.128.17 255.255.255.252
# classe mpls-interface
    mpls ip
# fin classe mpls-interface
# classe ospf6-interface
    ipv6 ospf 1 area 0
# fin classe ospf6-interface
# classe ospf4-interface
    ip ospf 2 area 0
# fin classe ospf4-interface
#template specifique a cette interface
  exit
# fin interface f4/0
#--
interface f0/0
    description connectee a f3/0 de  R4
    no shutdown
    ipv6 enable
    ipv6 address 2001:a151::1/64
    ip address 172.30.128.21 255.255.255.252
# classe mpls-interface
    mpls ip
# fin classe mpls-interface
# classe ospf6-interface
    ipv6 ospf 1 area 0
# fin classe ospf6-interface
# classe ospf4-interface
    ip ospf 2 area 0
# fin classe ospf4-interface
#template specifique a cette interface
    no ipv6 ospf 1 area 1
  exit
# fin interface f0/0
#--
# les templates provenant des classes seront remplaces a la 2e passe de templating
# classe ospf6-router
ipv6 router ospf 1
    redistribute connected
    router-id 10.0.0.10
  exit
#--
# fin classe ospf6-router
!
# classe bgp-router
router bgp 101
    bgp router-id 10.0.0.10
    neighbor 172.30.128.1 remote-as 102
    address-family ipv6 unicast
        neighbor 2001:b399::1 remote-as 102
        neighbor 2001:b399::1 activate
    exit-address-family
    neighbor 172.30.128.1 activate
    neighbor 172.30.128.14 remote-as 104
    address-family ipv6 unicast
        neighbor 2001:b6c1::2 remote-as 104
        neighbor 2001:b6c1::2 activate
    exit-address-family
    neighbor 172.30.128.14 activate
    neighbor 172.30.128.18 remote-as 103
    address-family ipv6 unicast
        neighbor 2001:acf4::2 remote-as 103
        neighbor 2001:acf4::2 activate
    exit-address-family
    neighbor 172.30.128.18 activate
    neighbor 172.30.128.22 remote-as 105
    address-family ipv6 unicast
        neighbor 2001:a151::2 remote-as 105
        neighbor 2001:a151::2 activate
    exit-address-family
    neighbor 172.30.128.22 activate
    address-family ipv4 unicast
        redistribute connected
    exit-address-family
    address-family ipv6 unicast
        redistribute connected
    exit-address-family
exit
!
#--
# fin classe bgp-router
!
# classe mpls-router
ip cef
ipv6 cef
#--
# fin classe mpls-router
!
# classe ospf4-router
router ospf 2
            router-id 10.0.0.10
            redistribute connected subnets
            exit
#--
# fin classe ospf4-router
!
# template specifique
#RR11
router ospf 2
 network 192.168.0.0 255.255.255.0 area 0
exit
# fin de la configuration de R1
```

