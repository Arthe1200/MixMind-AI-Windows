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

Les intégrations Spotify, Apple Music, Deezer et YouTube dépendront des API officielles, des conditions de service et des droits applicables. Un abonnement musical ne donne pas automatiquement accès aux fichiers audio bruts.

## Principes

- **Local d'abord :** les fichiers audio et la bibliothèque restent sur le PC, sauf action explicite de l'utilisateur.
- **IA facultative :** l'analyse audio et le moteur de mixage ne doivent pas dépendre obligatoirement de Grok.
- **Sécurité :** ne jamais committer de clés API, mots de passe, fichiers audio privés ou données personnelles.
- **Transparence :** afficher les analyses estimées comme telles et permettre de corriger manuellement les points de mix.
- **Licences propres :** vérifier la licence des dépendances, modèles, jeux de données et fichiers audio.
- **Qualité audio :** le traitement temps réel doit rester indépendant des appels réseau et des tâches IA lentes.

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
