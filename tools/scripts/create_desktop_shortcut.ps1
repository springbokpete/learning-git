$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $scriptDir "dist\DocumentsSorter.exe"

if (-not (Test-Path $exePath)) {
    throw "EXE not found: $exePath`nBuild first with .\build_exe.ps1"
}

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Documents Sorter.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = Split-Path -Parent $exePath
$shortcut.IconLocation = $exePath
$shortcut.Description = "Sorts files in Documents by file type"
$shortcut.Save()

Write-Host "Shortcut created: $shortcutPath"
