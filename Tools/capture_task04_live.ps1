$marker = 'C:\UnrealProjects\Battleground\Saved\Task04FullAudit\viewport_camera_ready.txt'
$shot = 'C:\UnrealProjects\Battleground\Saved\Task04FullAudit\full_viewport.png'
$summary = 'C:\UnrealProjects\Battleground\Saved\Task04FullAudit\live_capture_summary.txt'
Remove-Item $marker -ErrorAction SilentlyContinue
Remove-Item $shot -ErrorAction SilentlyContinue
Remove-Item $summary -ErrorAction SilentlyContinue

$exe = 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe'
$procArgs = @(
  'C:\UnrealProjects\Battleground\Battleground.uproject',
  '/Game/Maps/LV_HampiBattleground',
  '-ExecCmds="py C:\UnrealProjects\Battleground\Tools\capture_task04_viewport.py"',
  '-windowed',
  '-ResX=1366',
  '-ResY=768',
  '-log'
)
$proc = Start-Process -FilePath $exe -ArgumentList $procArgs -PassThru
$ready = $false
for ($i = 0; $i -lt 90; $i++) {
  if (Test-Path $marker) { $ready = $true; break }
  Start-Sleep -Seconds 2
}

$lines = @()
$lines += "EDITOR_PID=$($proc.Id)"
$lines += "CAMERA_MARKER=$ready"
if (Test-Path $marker) { $lines += "MARKER_CONTENT=$(Get-Content $marker -Raw)" }

if ($ready) {
  Start-Sleep -Seconds 12
  Add-Type -AssemblyName System.Drawing
  Add-Type -AssemblyName System.Windows.Forms
  $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
  $bitmap.Save($shot, [System.Drawing.Imaging.ImageFormat]::Png)
  $graphics.Dispose()
  $bitmap.Dispose()
  $lines += "SCREENSHOT=$shot"
  $lines += "SCREEN=$($bounds.Width)x$($bounds.Height)"
} else {
  $lines += 'SCREENSHOT=SKIPPED'
}

Start-Sleep -Seconds 2
$logPath = 'C:\UnrealProjects\Battleground\Saved\Logs\Battleground.log'
$logLines = Get-Content $logPath -Tail 2500
$lines += '--- MATERIAL COMPILE ERRORS ---'
$matErrors = $logLines | Select-String -Pattern 'Failed to compile Material' | ForEach-Object { $_.Line } | Sort-Object -Unique
if ($matErrors) { $lines += $matErrors } else { $lines += 'NONE' }
$lines += '--- MAP CHECK ---'
$mapChecks = $logLines | Select-String -Pattern 'MapCheck: Map check complete' | ForEach-Object { $_.Line } | Select-Object -Last 5
if ($mapChecks) { $lines += $mapChecks } else { $lines += 'NONE' }
$lines += '--- HISM USAGE WARNINGS ---'
$usageWarnings = $logLines | Select-String -Pattern 'was missing the usage flag bUsedWithInstancedStaticMeshes' | ForEach-Object { $_.Line } | Sort-Object -Unique
if ($usageWarnings) { $lines += $usageWarnings } else { $lines += 'NONE' }

$lines | Set-Content $summary

try { $proc.CloseMainWindow() | Out-Null } catch {}
Start-Sleep -Seconds 8
if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
$lines -join "`n"
