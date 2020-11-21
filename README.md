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
Et vous avez votre réseau OSPF, BGP, mpls sans effort !

## Personaliser des parties de la configuration
Le fichier `config.py` vous permet de rajouter votre grain de sel.

Pour trouver les noms des interfaces, activez *View > Show/Hide interfaces labels*
```python


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

### J'arrive plus à cliquer sur les routeurs pour accéder à la console !
Utilisez le bouton *Control > Console connect to all nodes*

## TODO
 * [ ] pouvoir tagger les routeurs & interfaces en groupes
 * [x] faire en sorte que l'utilisateur fournisse les templates (jinja2 ? pug ?)
 * [ ] pouvoir assigner des coûts aux liens pour du Traffic engineering (et les afficher avec des dessins GNS3)
 * [ ] configurer les conteneurs Docker
 * [ ] avoir un GUI ? (mdr)
 * [ ] option pour générer juste un squelette des configs ?
 * [x] générer des adresses IPv4 qui font des réseaux en /30 pour être + économe

----
> est-ce que j'ai gagné du temps en automatisant mon travail ? c'est pas sûr