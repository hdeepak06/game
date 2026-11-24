param(
    [string]$Title = "Hampi Battleground",
    [string]$Message = "Task notification",
    [string]$IconType = "Info"
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$notify = New-Object System.Windows.Forms.NotifyIcon
switch ($IconType.ToLower()) {
    "error" { $notify.Icon = [System.Drawing.SystemIcons]::Error }
    "warning" { $notify.Icon = [System.Drawing.SystemIcons]::Warning }
    default { $notify.Icon = [System.Drawing.SystemIcons]::Information }
}

$notify.BalloonTipTitle = $Title
$notify.BalloonTipText = $Message
$notify.Visible = $True
$notify.ShowBalloonTip(3500)
Start-Sleep -Milliseconds 2500
$notify.Dispose()
