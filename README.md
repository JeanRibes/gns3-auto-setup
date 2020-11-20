Ce script python se connecte au serveur GNS3 local et configure entièrement 
un réseau OSPF sur tous les routeurs. Il effectue tout seul l'adressage IP, l'allocation
des ``router-id``. 

Il s'adapte à n'importe quelle topologie réseau,
et vous êtes libre de choisir le nom de vos routeurs ! 
Il est possible de rajouter une configuration personnalisée pour rajouter une configuration
en plus par routeur ou même par interface.

Le script génère des configurations Cisco et les applique tout seul aux routeurs via la 
console telnet GNS3
# Installation
```
pip3 install gns3fy==0.7.1
```
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
Et vous avez votre réseau OSPF sans effort !

## Personaliser des parties de la configuration
Le fichier `config.py` vous permet de rajouter votre grain de sel.

Pour trouver les noms des interfaces, activez *View > Show/Hide interfaces labels*
```python
OSPF_AREA = '0'
OSPF_PROCESS = 1

config_custom = {  # permet de rajouter des paramètres personalisés
    'R8': {  # nom (hostname) du routeur. je vais modifier la configuration du routeur R8 ici
        'disable': False,  # désactive la configuration auto de ce routeur
        'router_id_override': '8.8.0.8',  # pour changer les router-id à la main
        'extra': "ipv6 router rip OUI\nredistribute connected",  # pour rajouter une configuration globale au routeur.
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
    'R1': {
        'disable': True
    }
}

```

## Recommandation
Ça marche avec des routeurs Cisco `c7200` avec les interfaces `PA-FE-TX`. J'ai pas testé le reste

# Fonctionnalités
## Réseau déployé
Déploie automatiquement un réseau OSPF IPv6 et IPv4 en activant ``ip cef`` et `mpls`.

## Diagramme dans GNS3
Ce script crée automatiquement des petites étiquettes/dessins dans GNS3 pour afficher le
sous-réseau actif sur un lien (IPv4 et IPv6).
Il affiche aussi le router-id par dessus l'icône du routeur.
### Je peux pas bouger les dessins
C'est normal, ils sont verrouillées pour que le script les retrouve et puisse les supprimer.
Si vous voulez tous les enlever, rajoutez ``exit(0)`` après `delete_drawings(project)` (ligne 196 `main.py`). Pour les bouger il suffit de faire clic droit > *Unlock item*.

Mais si vous faites ça il faudra les supprimer à la main.

## TODO
* rajouter une configuration utilisateur par lien, qui s'applique aux deux interfaces
(et aux deux routeurs) de chaque côté du lien. exemple:
```python
{
    'links': [
        {
            'link': 'R1-R2',
            'extra_router': """no ipv6 router rip""",
            'extra_interface': 'no shut',
            'override_network6': '2001:100:4',
            'override_network4': '192.168.5'
        },
        {'link': 'R4-R3',
         'disable': True}
    ]
}
```
* configurer les conteneurs Docker
* avoir un GUI ? (mdr)
* option pour générer juste un squelette des configs ?

----
> est-ce que j'ai gagné du temps en automatisant mon travail ? c'est pas sûr