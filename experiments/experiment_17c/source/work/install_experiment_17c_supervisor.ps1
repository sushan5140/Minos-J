# Installs the session-independent Experiment 17-C supervisor (Windows Task Scheduler, current user).
#
#   Preview only (changes nothing):  powershell -ExecutionPolicy Bypass -File work\install_experiment_17c_supervisor.ps1 -DryRun
#   Install:                         powershell -ExecutionPolicy Bypass -File work\install_experiment_17c_supervisor.ps1
#   Remove manually at any time:     schtasks /Delete /TN MinosJ-Experiment17C-Supervisor /F
#
# Creates exactly two tasks, both in the root folder, both for the current user only:
#   1. MinosJ-Experiment17C-Selftest   - runs once, then this script deletes it (auto-deletes after 30 min regardless).
#   2. MinosJ-Experiment17C-Supervisor - every 30 min; deletes itself when 17-C is complete and validated;
#                                        disables itself after 3 consecutive failures or an integrity refusal;
#                                        Windows deletes it automatically after its 21-day end boundary.
# No other task, service, registry key, startup entry or setting is created or modified.
# No password is stored (runs only while you are logged on). Least privilege (not elevated).

param([switch]$DryRun)
$ErrorActionPreference = "Stop"

$W  = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $Py)) { throw "Python not found at $Py" }
$User  = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Fmt   = "yyyy-MM-ddTHH:mm:ss"
$Now   = Get-Date

function Task-Xml([string]$Description, [string]$Arguments, [datetime]$Start, [datetime]$End, [string]$Repetition) {
@"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>$Description</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>$($Start.ToString($Fmt))</StartBoundary>
      <EndBoundary>$($End.ToString($Fmt))</EndBoundary>
      <Enabled>true</Enabled>$Repetition
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$User</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <DeleteExpiredTaskAfter>PT0S</DeleteExpiredTaskAfter>
    <WakeToRun>false</WakeToRun>
    <Hidden>false</Hidden>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>conhost.exe</Command>
      <Arguments>$Arguments</Arguments>
      <WorkingDirectory>$W</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
}

$SelftestXml = Task-Xml "Minos-J Experiment 17-C supervisor self-test (one tiny non-experimental Claude call; not in the ledger)." `
    "--headless &quot;$Py&quot; work\experiment_17c_tick.py --selftest" $Now.AddMinutes(10) $Now.AddMinutes(30) ""
$SupervisorXml = Task-Xml "Resumes Minos-J Experiment 17-C every 30 minutes until complete and validated, then deletes itself." `
    "--headless &quot;$Py&quot; work\experiment_17c_tick.py" $Now.AddMinutes(2) $Now.AddDays(21) @"

      <Repetition>
        <Interval>PT30M</Interval>
        <Duration>P21D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
"@

if ($DryRun) {
    "=== DRY RUN: no task is created. The install would register exactly these two tasks as $User ==="
    "`n--- Task 1: \MinosJ-Experiment17C-Selftest (started immediately, then deleted by this script) ---"
    $SelftestXml
    "`n--- Task 2: \MinosJ-Experiment17C-Supervisor ---"
    $SupervisorXml
    return
}

# 1. Self-test from the Task Scheduler context. Abort before installing the supervisor if it fails.
Register-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest" -Xml $SelftestXml -Force | Out-Null
Start-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest"
$deadline = (Get-Date).AddMinutes(5)
Start-Sleep 3
while ((Get-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest").State -eq "Running" -and (Get-Date) -lt $deadline) { Start-Sleep 5 }
Stop-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest" -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "MinosJ-Experiment17C-Selftest" -Confirm:$false
$result = Join-Path $W "work\experiment_17c_supervisor_selftest.json"
if (-not (Test-Path $result) -or (Get-Item $result).LastWriteTime -lt $Now) { throw "Self-test produced no fresh result; supervisor NOT installed." }
Get-Content $result
$st = Get-Content $result -Raw | ConvertFrom-Json
if ($null -eq $st.structured_output -or $st.structured_output.answer -ne 4) { throw "Self-test failed; supervisor NOT installed." }

# 2. The recurring supervisor.
Register-ScheduledTask -TaskName "MinosJ-Experiment17C-Supervisor" -Xml $SupervisorXml -Force | Out-Null
Get-ScheduledTask -TaskName "MinosJ-Experiment17C-*" | Select-Object TaskPath, TaskName, State
