# Contribuer à MixMind AI

Merci de contribuer !

- Ouvrir une issue avant un changement important.
- Garder interface, analyse et moteur audio séparés.
- Ajouter des tests aux fonctions testables sans interface.
- Ne jamais committer de clés API, de fichiers audio privés ou de données personnelles.
- Vérifier les licences des dépendances, modèles et jeux de données.
- Décrire les limites connues ; ne pas présenter une transition calculée comme garantie professionnelle sans validation d'écoute.

## Développement local

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
ruff check .
```

Les pull requests doivent décrire le problème, la solution, les tests et les plateformes testées. Les changements audio doivent préciser les formats pris en charge et les cas d'erreur.
