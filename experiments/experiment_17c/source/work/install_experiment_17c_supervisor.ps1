# Installs the session-independent Experiment 17-C supervisor (Windows Task Scheduler, current user).
#
#   Preview only (changes nothing):  powershell -ExecutionPolicy Bypass -File work\install_experiment_17c_supervisor.ps1 -DryRun
#   Install:                         powershell -ExecutionPolicy Bypass -File work\install_experiment_17c_supervisor.ps1
#   Remove manually at any time:     schtasks /Delete /TN MinosJ-Experiment17C-Supervisor /F
#
# Creates exactly two tasks, both in the root folder, both for the current user only:
#   1. MinosJ-Experiment17C-Selftest   - no trigger (on demand only); started explicitly by this script,
#                                        awaited until Task Scheduler reports it ran and finished, then deleted.
#   2. MinosJ-Experiment17C-Supervisor - registered ONLY if the self-test PASSES. Every 30 min; deletes itself
#                                        when 17-C is complete and validated; disables itself after 3 consecutive
#                                        failures or an integrity refusal; Windows deletes it after its 21-day end.
# No other task, service, registry key, startup entry or setting is created or modified.
# No password is stored (runs only while you are logged on). Least privilege (not elevated).
# Every install attempt writes work\experiment_17c_install_diagnostics\install_<timestamp>.json.

param([switch]$DryRun)
$ErrorActionPreference = "Stop"

$W  = Split-Path -Parent $PSScriptRoot
$Py = "C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $Py)) { throw "Python not found at $Py" }
$User = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Fmt  = "yyyy-MM-ddTHH:mm:ss"
$Now  = Get-Date
$SelfName = "MinosJ-Experiment17C-Selftest"
$SupName  = "MinosJ-Experiment17C-Supervisor"

function Task-Xml([string]$Description, [string]$Arguments, [string]$TriggersXml, [bool]$DeleteWhenExpired) {
    $expire = if ($DeleteWhenExpired) { "`n    <DeleteExpiredTaskAfter>PT0S</DeleteExpiredTaskAfter>" } else { "" }
@"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>$Description</Description>
  </RegistrationInfo>$TriggersXml
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
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>$expire
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

$SelftestXml = Task-Xml "Minos-J Experiment 17-C supervisor self-test (one tiny non-experimental Claude call; not in the ledger). On demand only." `
    "--headless &quot;$Py&quot; work\experiment_17c_tick.py --selftest" "" $false
$SupervisorTriggers = @"

  <Triggers>
    <TimeTrigger>
      <StartBoundary>$($Now.AddMinutes(2).ToString($Fmt))</StartBoundary>
      <EndBoundary>$($Now.AddDays(21).ToString($Fmt))</EndBoundary>
      <Enabled>true</Enabled>
      <Repetition>
        <Interval>PT30M</Interval>
        <Duration>P21D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </TimeTrigger>
  </Triggers>
"@
$SupervisorXml = Task-Xml "Resumes Minos-J Experiment 17-C every 30 minutes until complete and validated, then deletes itself." `
    "--headless &quot;$Py&quot; work\experiment_17c_tick.py" $SupervisorTriggers $true

if ($DryRun) {
    "=== DRY RUN: no task is created. The install would register at most these two tasks as $User ==="
    "`n--- Task 1: \$SelfName (no trigger; started explicitly, awaited, then deleted) ---"
    $SelftestXml
    "`n--- Task 2: \$SupName (registered only if the self-test passes) ---"
    $SupervisorXml
    return
}

# ---------------------------------------------------------------- self-test
$Diag   = Join-Path $W "work\experiment_17c_install_diagnostics"
New-Item -ItemType Directory -Force $Diag | Out-Null
$Stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$Report = Join-Path $Diag "install_$Stamp.json"
$Result = Join-Path $W "work\experiment_17c_supervisor_selftest.json"
$ErrTxt = Join-Path $W "work\experiment_17c_selftest_error.txt"
$SupLog = Join-Path $W "work\experiment_17c_supervisor.log"
# Move any earlier result aside so "fresh result" is unambiguous (preserved, not deleted).
foreach ($f in @($Result, $ErrTxt)) { if (Test-Path $f) { Move-Item $f (Join-Path $Diag ("previous_{0}_{1}" -f $Stamp, (Split-Path $f -Leaf))) } }

$timeline = New-Object System.Collections.ArrayList
$diagnostics = [ordered]@{ started_at = $Now.ToString("o"); user = $User; python = $Py; working_directory = $W }
$ran = $false; $finished = $false; $timedOut = $false

Register-ScheduledTask -TaskName $SelfName -Xml $SelftestXml -Force | Out-Null
$registeredAt = Get-Date
$diagnostics.registered_at = $registeredAt.ToString("o")
try {
    Start-ScheduledTask -TaskName $SelfName
    $diagnostics.start_requested_at = (Get-Date).ToString("o")
    $deadline = (Get-Date).AddMinutes(6)
    do {
        Start-Sleep -Seconds 2
        $task = Get-ScheduledTask -TaskName $SelfName
        $info = Get-ScheduledTaskInfo -TaskName $SelfName
        [void]$timeline.Add([ordered]@{ at = (Get-Date).ToString("o"); state = "$($task.State)";
            last_run_time = $info.LastRunTime.ToString("o"); last_task_result = ('0x{0:X}' -f $info.LastTaskResult) })
        # A new task reports LastRunTime 1999-11-30 until Task Scheduler actually launches it.
        $ran = $info.LastRunTime -ge $registeredAt.AddSeconds(-2)
        $finished = $ran -and ("$($task.State)" -notin @("Running", "Queued"))
    } until ($finished -or (Get-Date) -gt $deadline)
    if (-not $finished) {
        $timedOut = $true
        Stop-ScheduledTask -TaskName $SelfName -ErrorAction SilentlyContinue
    }
    $info = Get-ScheduledTaskInfo -TaskName $SelfName
    $diagnostics.final_last_run_time = $info.LastRunTime.ToString("o")
    $diagnostics.final_last_task_result = ('0x{0:X}' -f $info.LastTaskResult)
} finally {
    Unregister-ScheduledTask -TaskName $SelfName -Confirm:$false -ErrorAction SilentlyContinue
    $diagnostics.selftest_task_deleted_at = (Get-Date).ToString("o")
}

$pythonStarted = $false
if (Test-Path $SupLog) {
    foreach ($line in Get-Content $SupLog) {
        if ($line -match '^(\S+Z) .*selftest started') {
            if ([datetime]::Parse($Matches[1]).ToLocalTime() -ge $registeredAt.AddSeconds(-2)) { $pythonStarted = $true }
        }
    }
}
$selftest = if (Test-Path $Result) { Get-Content $Result -Raw | ConvertFrom-Json } else { $null }

$classification =
    if (-not $ran) { "SCHEDULING_FAILURE: Task Scheduler never launched the self-test task" }
    elseif (-not $pythonStarted) { "LAUNCHER_FAILURE: task ran (LastTaskResult $($diagnostics.final_last_task_result)) but Python never started" }
    elseif ($timedOut) { "TIMEOUT: self-test still running after 6 minutes" }
    elseif (Test-Path $ErrTxt) { "SELFTEST_CRASH: see work\experiment_17c_selftest_error.txt" }
    elseif ($null -eq $selftest) { "NO_RESULT: Python started but wrote no result" }
    elseif ($selftest.is_error -or $null -eq $selftest.structured_output) { "CLAUDE_CLI_OR_AUTH_FAILURE: $($selftest.error_text)" }
    elseif ($selftest.structured_output.answer -ne 4) { "WRONG_OUTPUT: $($selftest.structured_output | ConvertTo-Json -Compress)" }
    else { "PASS" }

$diagnostics.task_ran = $ran; $diagnostics.task_finished = $finished; $diagnostics.timed_out = $timedOut
$diagnostics.python_started = $pythonStarted; $diagnostics.state_timeline = $timeline
$diagnostics.selftest_result = $selftest; $diagnostics.classification = $classification
if (Test-Path $ErrTxt) { $diagnostics.selftest_traceback = [System.IO.File]::ReadAllText($ErrTxt) }
$diagnostics | ConvertTo-Json -Depth 6 | Set-Content -Path $Report -Encoding utf8

"Self-test: $classification"
"Diagnostics: $Report"
if ($classification -ne "PASS") {
    throw "Self-test did not pass ($classification). Supervisor NOT installed. Diagnostics preserved in $Report"
}

# ---------------------------------------------------------------- supervisor (only after PASS)
Register-ScheduledTask -TaskName $SupName -Xml $SupervisorXml -Force | Out-Null
Get-ScheduledTask -TaskName $SupName | Select-Object TaskPath, TaskName, State
"Supervisor installed. First tick in about 2 minutes; log: work\experiment_17c_supervisor.log"
