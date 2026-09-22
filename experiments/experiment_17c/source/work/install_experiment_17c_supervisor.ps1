# Installs the session-independent Experiment 17-C supervisor as a Windows
# scheduled task for the current user. Run it yourself in PowerShell:
#   powershell -ExecutionPolicy Bypass -File work\install_experiment_17c_supervisor.ps1
# Remove later with:
#   Unregister-ScheduledTask -TaskName MinosJ-Experiment17C-Supervisor -Confirm:$false
#
# - Runs work\experiment_17c_tick.py every 30 minutes, whether or not the
#   Claude app is open (you must be logged in to Windows; no password stored).
# - Never starts a second instance while a tick is running; the tick itself
#   exits if an Experiment 17-C run is already active.
# - Runs on battery; no time limit; hidden console (conhost --headless).
# - Then runs a one-shot self-test from the scheduler context and prints it.

$ErrorActionPreference = "Stop"
$W  = Split-Path -Parent $PSScriptRoot
$Py = (Get-Command python).Source
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
             -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

# 1. One-shot self-test from the scheduler context (non-experimental, ~1k tokens).
$self = New-ScheduledTaskAction -Execute "conhost.exe" -Argument "--headless `"$Py`" work\experiment_17c_tick.py --selftest" -WorkingDirectory $W
Register-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest" -Action $self -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest"
$deadline = (Get-Date).AddMinutes(5)
while ((Get-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest").State -eq "Running" -and (Get-Date) -lt $deadline) { Start-Sleep 5 }
Unregister-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest" -Confirm:$false
Get-Content (Join-Path $W "work\experiment_17c_supervisor_selftest.json")

# 2. The recurring supervisor: every 30 minutes, indefinitely.
$tick    = New-ScheduledTaskAction -Execute "conhost.exe" -Argument "--headless `"$Py`" work\experiment_17c_tick.py" -WorkingDirectory $W
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "MinosJ-Experiment17C-Supervisor" -Action $tick -Trigger $trigger -Settings $settings `
    -Principal $principal -Description "Resumes Minos-J Experiment 17-C every 30 minutes until complete and validated." -Force | Out-Null
Get-ScheduledTask -TaskName "MinosJ-Experiment17C-Supervisor" | Select-Object TaskName, State
