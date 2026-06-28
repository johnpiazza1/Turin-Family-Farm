# Registers a Windows Task Scheduler job to run the weekly apiary report
# every Sunday at 8:00 AM.
#
# Usage (run as Administrator in PowerShell):
#   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\schedule_windows.ps1

$PythonPath = (Get-Command python).Source
$ScriptPath = Join-Path $PSScriptRoot "main.py"
$TaskName   = "BeehiveCommandWeeklyReport"
$WorkingDir = $PSScriptRoot

$Action  = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

$Trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Sunday `
    -At "08:00AM"

$Settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -RunLevel Highest `
    -Force

Write-Host "Task '$TaskName' registered. Next run: Sunday 8:00 AM."
Write-Host "Verify with: Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
