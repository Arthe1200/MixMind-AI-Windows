# MixMind AI

**Un assistant DJ open source pour Windows : analyser, préparer et mixer des morceaux avec une IA locale ou l'API Grok.**

> **État du projet :** démarrage du développement. Cette première étape prépare l'architecture ; elle ne prétend pas encore fournir un moteur DJ professionnel complet.

## Vision

MixMind AI vise une application de bureau Windows, et non un simple site web. À terme, le logiciel devra permettre de :

- importer et organiser des fichiers audio que l'utilisateur est autorisé à utiliser ;
- analyser le tempo (BPM), la tonalité et la structure des morceaux ;
- proposer des transitions avec des points d'entrée et de sortie explicites ;
- mixer et exporter l'audio à l'aide d'un moteur dédié ;
- choisir entre des fonctions IA locales et un fournisseur distant facultatif (Grok) ;
- conserver la bibliothèque et les projets sur le PC.

**Intégrations catalogue présentes dans l'application :** Deezer (recherche publique), Spotify (recherche API avec Client ID/Secret), Apple Music (catalogue avec Developer Token) et YouTube Music (recherche via YouTube Data API). Les résultats s'ouvrent sur la plateforme officielle. Les clés API ne sont pas incluses dans le dépôt. Un abonnement musical ne donne pas automatiquement accès aux fichiers audio bruts.

## Fonctionnalités de la workstation DJ

- **Deux platines indépendantes A/B** : charger et lire deux fichiers locaux simultanément, avec pause, stop, cue au début et barre de position/durée pour chaque platine.
- **Crossfader audio réel** à courbe de puissance égale, avec niveau master et gain indépendant par platine.
- **Pitch / vitesse** réglable par platine. La vitesse et la hauteur changent ensemble dans cette première implémentation.
- **Synchronisation BPM manuelle** : saisir les BPM connus de A et B, puis synchroniser la vitesse de B. Il ne s'agit pas encore d'une détection BPM automatique ni d'une synchronisation de phase.
- Bibliothèque locale avec import multiple, scan récursif de dossier, recherche et retrait sans supprimer les fichiers d'origine.
- Raccourcis : `Ctrl+O` importer, `Ctrl+F` rechercher, `Ctrl+1` charger sur A, `Ctrl+2` charger sur B, `Espace` commande de lecture rapide.

**Limites actuelles :** ce socle permet de lire deux pistes et de les fondre réellement, mais il ne dispose pas encore de formes d'onde, de détection automatique BPM/tonalité, d'EQ/filtre DSP, de préécoute casque indépendante, de boucles/hot cues ni d'export de remix. Ces éléments nécessitent des composants audio dédiés et seront ajoutés ensuite.

## Fonctionnalités déjà présentes dans l'interface

- Importer plusieurs fichiers audio locaux ou scanner un dossier et ses sous-dossiers.
- Rechercher rapidement un titre dans la bibliothèque de la session.
- Préécouter un morceau, mettre en pause, arrêter et régler le volume.
- Barre de progression avec durée écoulée/totale et déplacement dans le morceau.
- Navigation précédent/suivant, lecture aléatoire et répétition.
- Retirer un titre de la liste sans supprimer le fichier audio d'origine.
- Raccourcis clavier : `Espace` lecture/pause, `Ctrl+O` import, `Ctrl+F` recherche, `Suppr` retirer, `Alt+←/→` précédent/suivant.
- Mémoriser le volume et la taille/position de la fenêtre entre les lancements.

Ces commandes améliorent la bibliothèque et la préécoute, mais ne constituent pas encore un mixeur DJ à deux platines. Le BPM automatique, les formes d'onde, les effets, le crossfader et l'export de remixes restent à développer.

## Plateformes musicales

Dans l'application, ouvre l'onglet **Plateformes**, choisis Deezer, Spotify, Apple Music ou YouTube Music, puis lance une recherche. Double-clique un résultat pour ouvrir le titre dans le service officiel. Le bouton **Recherche sur le site (sans clé API)** ouvre aussi directement la recherche officielle si tu ne veux pas configurer les API.

- **Deezer :** la recherche publique est utilisée sans clé configurée.
- **Spotify :** crée une application sur le [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), puis saisis le Client ID et le Client Secret dans « Configurer les API ».
- **Apple Music :** un Apple Music Developer Token valide est nécessaire pour interroger le catalogue.
- **YouTube Music :** active YouTube Data API v3 dans un projet Google Cloud et saisis la clé API dans « Configurer les API ».

Les clés sont conservées dans les paramètres locaux de l'utilisateur Windows et **ne sont pas chiffrées par l'application** : ne partage pas ton compte Windows ni ses paramètres. Ne committe jamais de clés dans GitHub.

**Limite volontaire :** ces intégrations recherchent le catalogue et ouvrent les pages officielles ; elles ne déverrouillent pas les flux audio protégés et ne chargent pas automatiquement les morceaux en platine. Pour mixer, importe des fichiers audio locaux que tu es autorisé à utiliser. Les accès API peuvent être soumis à l'éligibilité développeur, quotas, changements de politique ou validation par les plateformes.

## Principes

- **Local d'abord :** les fichiers audio et la bibliothèque restent sur le PC, sauf action explicite de l'utilisateur.
- **IA facultative :** l'analyse audio et le moteur de mixage ne doivent pas dépendre obligatoirement de Grok.
- **Sécurité :** ne jamais committer de clés API, mots de passe, fichiers audio privés ou données personnelles.
- **Transparence :** afficher les analyses estimées comme telles et permettre de corriger manuellement les points de mix.
- **Licences propres :** vérifier la licence des dépendances, modèles, jeux de données et fichiers audio.
- **Qualité audio :** le traitement temps réel doit rester indépendant des appels réseau et des tâches IA lentes.

## Fondations techniques ajoutées

- core/audio/mixer.py : calculs testés de crossfader à puissance égale et gains par canal/master. Ce module calcule les niveaux mais ne constitue pas à lui seul un moteur de mixage de buffers audio.
- core/hardware/midi.py : profils MIDI JSON, validation des messages, associations bouton/action et dispatcher testable sans matériel. Dépendances matérielles optionnelles via pip install -e ".[hardware]".
- core/analysis/analyzer.py : estimation BPM et résumé de forme d'onde via les dépendances optionnelles d'analyse. L'analyse doit tourner en tâche de fond ; les BPM restent des estimations.
- Tests unitaires du crossfader, des gains et des profils MIDI.

Ces modules sont des fondations réelles, mais le moteur DSP temps réel, la détection matérielle, tous les effets, les stems IA et les connexions OAuth ne sont pas encore intégrés à l'interface.

## Architecture prévue

- `app/` : lancement et interface PySide6.
- `core/audio/` : lecture, mixage, effets et export.
- `core/analysis/` : analyse des morceaux.
- `core/transitions/` : planification des transitions.
- `core/ai/` : interface commune aux fournisseurs IA local et distant.
- `core/library/` : bibliothèque locale et métadonnées.
- `integrations/` : intégrations de services, uniquement lorsque leur accès est autorisé.
- `tests/` : tests automatisés.
- `docs/` : architecture, décisions et guide de contribution.

## Démarrage développeur

Prérequis : Windows 10/11 64 bits et Python 3.11 ou version compatible précisée dans `pyproject.toml`.

```powershell
git clone https://github.com/Arthe1200/MixMind-AI-Windows.git
cd MixMind-AI-Windows
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m mixmind
```

Les commandes de lancement seront activées au fur et à mesure que les modules correspondants seront implémentés.

## Configuration Grok

Le mode Grok est facultatif. Si activé, configurez la clé dans les paramètres locaux de l'application ou dans une variable d'environnement telle que `XAI_API_KEY`. Ne mettez jamais cette clé dans le code source ni dans Git. Les appels à une API peuvent être payants et nécessitent une connexion Internet.

## Licence

Le code du projet est destiné à être distribué sous licence MIT. Les dépendances, modèles IA, jeux de données et contenus audio restent soumis à leurs propres licences et conditions.

Voir [LICENSE](LICENSE).
