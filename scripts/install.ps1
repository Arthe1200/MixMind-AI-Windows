$ErrorActionPreference = "Stop"

Write-Host "MixMind AI - installation de l'environnement développeur" -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher introuvable. Installe Python 3.11 puis relance ce script."
}

py -3.11 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Échec de création de l'environnement virtuel." }

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Échec de mise à jour de pip." }

& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) { throw "Échec d'installation de MixMind AI." }

Write-Host "Installation terminée. Lance l'application avec : .\.venv\Scripts\mixmind.exe" -ForegroundColor Green
