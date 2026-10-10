$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Environnement absent. Exécute d'abord .\scripts\install.ps1"
}

& .\.venv\Scripts\python.exe -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Échec d'installation de PyInstaller." }

& .\.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --name "MixMind AI" --collect-all PySide6 --paths src src\mixmind\main.py
if ($LASTEXITCODE -ne 0) { throw "Échec de génération de l'exécutable." }

Write-Host "Build terminé dans dist. Teste l'exécutable sur un PC Windows propre avant publication." -ForegroundColor Green
