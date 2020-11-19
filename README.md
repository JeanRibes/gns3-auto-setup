Ce script python se connecte au serveur GNS3 local et configure entièrement 
un réseau OSPF sur tous les routeurs. Il effectue tout seul l'adressage IP, l'allocation
des ``router-id``.
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
* faites Ok

# Utilisation
* Ouvrez votre projet
* Lancez votre projet (si c'est déjà pas besoin de relancer)
* Attendez que les routeurs démarrent
* Lancez le script
* Attendez que les routeurs se découvrent et propagent leurs routes
Et vous avez votre réseau OSPF tout fait !

## Recommandation
Ça marche avec des routeurs Cisco `c7200` avec les interfaces `PA-FE-TX`. J'ai pas testé le reste

# Fonctionnalités
## Réseau déployé
Déploie un réseau OSPF IPv6 et IPv4 en activant ``ip cef`` et `mpls`.

## Diagramme dans GNS3
Ce script crée automatiquement des petites étiquettes/dessins dans GNS3 pour afficher le
sous-réseau actif sur un lien (IPv4 et IPv6).
Il affiche aussi le router-id par dessus l'icône du routeur.
### Je peux pas bouger les dessins
C'est normal, ils sont verrouillées pour que le script les retrouve et puisse les supprimer.
Si vous voulez tous les enlever, rajoutez ``exit(0)`` après `delete_drawings(project)` (ligne 196 `main.py`). Pour les bouger il suffit de faire clic droit > *Unlock item*.

Mais si vous faites ça il faudra les supprimer à la main.


----
> est-ce que j'ai gagné du temps en automatisant mon travail ? c'est pas sûr