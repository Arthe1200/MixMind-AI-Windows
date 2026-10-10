# Architecture

## Règle centrale

Le moteur audio temps réel ne doit jamais attendre une réponse IA ou un appel réseau. L'IA propose un plan ; le moteur audio exécute des paramètres validés par l'application.

## Couches

1. **UI (PySide6)** : commandes et visualisation.
2. **Services applicatifs** : projets, bibliothèque, paramètres et tâches.
3. **Audio** : lecture, transport, mixage, effets et export.
4. **Analyse** : BPM, battements, tonalité et structure. Les estimations doivent être présentées comme telles.
5. **Planificateur de transitions** : propose des points de transition et des automations modifiables.
6. **Fournisseurs IA** : contrat commun pour les modèles locaux et distants ; aucun fournisseur ne contrôle directement le matériel audio.
7. **Persistance** : SQLite pour métadonnées et projets ; les médias restent dans les emplacements choisis par l'utilisateur.

## Confidentialité et sécurité

- Clés API uniquement dans les paramètres locaux ou variables d'environnement.
- Ne pas envoyer les fichiers audio à un service distant sans consentement explicite.
- Les appels distants doivent transmettre uniquement les données nécessaires.
- Les intégrations musicales doivent utiliser des API officielles et respecter leurs conditions.

## Jalons

- V0.1 : préécoute d'un fichier et import local.
- V0.2 : analyse BPM/structure et suggestions de transitions.
- V0.3 : transport multi-platines, synchronisation et crossfade.
- V0.4 : séparation de sources et arrangements plus avancés.
