$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python -m pip install -e ".[dev]"
python -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging/bc2800.spec

$exe = Join-Path (Get-Location) "dist\BC2800 Receptor\BC2800 Receptor.exe"
if (-not (Test-Path $exe)) {
    throw "Build failed: $exe not found"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "BC2800 Receptor.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = Split-Path $exe -Parent
$shortcut.Description = "Receptor serial da BC-2800Vet"
$shortcut.Save()

Write-Host "Build ok: $exe"
Write-Host "Atalho: $shortcutPath"
Write-Host "O programa cria a entrada de inicializacao do Windows na primeira execucao."
