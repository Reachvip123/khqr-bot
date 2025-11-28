# Redeploy helper script for KHQR bot on Railway
# Usage: Right-click > Run with PowerShell or execute: powershell -File .\redeploy.ps1

$ErrorActionPreference = 'Stop'

Write-Host "[Redeploy] Starting KHQR bot redeploy..."

# Navigate to script directory
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Optional syntax check
try {
  python -m py_compile khqrbot.txt
  Write-Host "[Redeploy] Syntax check passed."
} catch {
  Write-Host "[Redeploy] Syntax check failed:" $_.Exception.Message
  exit 1
}

# Add and commit changes
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
git add khqrbot.txt RAILWAY_DEPLOYMENT.md
if ($args.Length -gt 0) {
  $msg = $args -join ' '
} else {
  $msg = "Redeploy: $timestamp"
}

git commit -m $msg

try {
  git push origin main
  Write-Host "[Redeploy] Push complete. Railway should redeploy shortly." -ForegroundColor Green
} catch {
  Write-Host "[Redeploy] Push failed. Ensure remote is set (git remote -v)." -ForegroundColor Red
  exit 1
}
