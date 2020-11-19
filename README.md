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
* Éditez le script pour mettre le nom de votre projet GNS3 (``GNS3_PROJECT_NAME``).
* Ouvrez votre projet
* Lancez votre projet (si c'est déjà pas besoin de relancer)
* Attendez que les routeurs démarrent
* Lancez le script
* Attendez que les routeurs se découvrent et propagent leurs routes
Et vous avez votre réseau OSPF tout fait !

## Recommandation
Ça marche avec des routeurs Cisco `c7200` avec les interfaces `PA-FE-TX`. J'ai pas testé le reste