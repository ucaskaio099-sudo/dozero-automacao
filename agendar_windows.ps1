# Agenda publicação local a cada 30 min (06:00-23:59).
# Requer .env com token Meta real e um host HTTPS para as imagens.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction Stop).Source
}
$Script = Join-Path $Root "scripts\publicar.py"
$TaskName = "DoZeroAoReal-Instagram"

$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" --incluir-atrasados --limite 2" -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
Write-Host "Tarefa agendada: $TaskName"
Write-Host "Roda: $Python $Script --incluir-atrasados --limite 2"
