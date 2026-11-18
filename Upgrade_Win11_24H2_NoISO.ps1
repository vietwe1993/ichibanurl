# Windows 11 24H2 -> 26H2 (if eligible), otherwise 25H2
# NO ISO / NO setup.exe. Installs Microsoft enablement packages (.msu) only.
# Run locally as SYSTEM or elevated Administrator (e.g. MeshCentral).
# Logs & downloads: D:\Win11Upgrade. See -NoAutoReboot for maintenance windows.
[CmdletBinding()]
param(
    [switch]$NoAutoReboot,
    [switch]$Prefer25H2,
    [switch]$Resume,
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$Root = 'D:\Win11Upgrade'
$LogDir = Join-Path $Root 'Logs'
$LogFile = Join-Path $LogDir '24H2_to_25H2_26H2.log'
$StatusFile = Join-Path $Root '24H2_upgrade_status.json'
$TaskName = 'Win11_24H2_Enablement_Continue'
$RebootCountFile = Join-Path $Root '24H2_reboot_count.txt'
$ScriptFile = $MyInvocation.MyCommand.Path
$Min25UBR = 5074   # Windows 11 24H2: KB5064081 or later
$Min26UBR = 9546   # Windows 11 24H2: KB5124010 or later

if (-not (Test-Path 'D:\')) { throw 'Drive D: does not exist. No changes made.' }
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Log([string]$Message) {
    $line = ('{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Message)
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}
function State([string]$Name, [string]$Details) {
    $current = Get-OSInfo
    $obj = [ordered]@{
        time = (Get-Date).ToString('o'); computer = $env:COMPUTERNAME
        state = $Name; details = $Details
        version = $current.Version; build = $current.Build; ubr = $current.UBR
    }
    $json = $obj | ConvertTo-Json -Depth 5
    $tmp = "$StatusFile.tmp"
    [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tmp -Destination $StatusFile -Force
    Log "STATE=$Name | $Details"
}
function Get-OSInfo {
    $r = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $b = 0; $u = 0
    if (-not [int]::TryParse([string]$r.CurrentBuildNumber, [ref]$b)) {
        [void][int]::TryParse([string]$r.CurrentBuild, [ref]$b)
    }
    [void][int]::TryParse([string]$r.UBR, [ref]$u)
    return [PSCustomObject]@{ Build = $b; UBR = $u; Version = [string]$r.DisplayVersion; Edition = [string]$r.EditionID }
}
function Is-RebootPending {
    return ((Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or
            (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired'))
}
function Schedule-Continue {
    if (-not $ScriptFile -or -not (Test-Path -LiteralPath $ScriptFile)) {
        throw 'Cannot register resume task: the .ps1 file must remain on D: after reboot.'
    }
    $flags = '-Resume'
    if ($NoAutoReboot) { $flags += ' -NoAutoReboot' }
    if ($Prefer25H2) { $flags += ' -Prefer25H2' }
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "{0}" {1}' -f $ScriptFile, $flags
    $action = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 6) -StartWhenAvailable
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Log "Scheduled SYSTEM resume task: $TaskName"
}
function Unschedule-Continue {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    }
}
function Restart-ForUpgrade([string]$Description) {
    $reboots = 0
    if (Test-Path -LiteralPath $RebootCountFile) {
        [void][int]::TryParse(([System.IO.File]::ReadAllText($RebootCountFile).Trim()), [ref]$reboots)
    }
    if ($reboots -ge 3) { throw 'Safety stop: already scheduled 3 upgrade restarts without success. Review logs before retrying.' }
    Schedule-Continue
    if ($NoAutoReboot) {
        State 'RESTART_REQUIRED' "$Description; restart Windows manually to continue."
        return
    }
    [System.IO.File]::WriteAllText($RebootCountFile, [string]($reboots + 1))
    State 'RESTART_SCHEDULED' "$Description; automatic restart in 5 minutes."
    & "$env:SystemRoot\System32\shutdown.exe" /r /t 300 /c 'Windows feature upgrade: installation will resume after restart. Save your work.' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Unable to schedule reboot (exit $LASTEXITCODE)" }
}
function Install-Required-LCU {
    State 'UPDATING_PREREQUISITE' 'Installed Windows 11 24H2 cumulative update is too old; trying Windows Update for an applicable newer LCU.'
    $session = New-Object -ComObject Microsoft.Update.Session
    $searcher = $session.CreateUpdateSearcher()
    $searcher.Online = $true
    $searcher.ServerSelection = 2
    $result = $searcher.Search("IsInstalled=0 and IsHidden=0 and Type='Software'")
    if ($result.ResultCode -ne 2) { throw "Windows Update search failed: $($result.ResultCode)" }
    $candidates = @()
    for ($i=0; $i -lt $result.Updates.Count; $i++) {
        $upd = $result.Updates.Item($i)
        Log "WUA: $($upd.Title)"
        if ($upd.Title -match '(?i)Cumulative Update for Windows 11.*24H2' -and $upd.Title -notmatch '(?i)\.NET|Preview') {
            $candidates += $upd
        }
    }
    if ($candidates.Count -eq 0) {
        throw 'No 24H2 cumulative update offered. Update the OS to build 26100.5074+ first; no ISO or bypass attempted.'
    }
    $selected = $candidates | Sort-Object LastDeploymentChangeTime -Descending | Select-Object -First 1
    Log "Downloading prerequisite: $($selected.Title)"
    if (-not $selected.EulaAccepted) { $selected.AcceptEula() }
    $collection = New-Object -ComObject Microsoft.Update.UpdateColl
    [void]$collection.Add($selected)
    $downloader = $session.CreateUpdateDownloader()
    $downloader.Updates = $collection
    $down = $downloader.Download()
    if ($down.ResultCode -ne 2) { throw "LCU download failed: $($down.ResultCode)" }
    $installer = $session.CreateUpdateInstaller()
    $installer.Updates = $collection
    $installed = $installer.Install()
    if ($installed.ResultCode -notin @(2,3)) { throw "LCU install failed: $($installed.ResultCode), hresult=$($installed.HResult)" }
    Log "Prerequisite LCU installed/staged; reboot required=$($installed.RebootRequired)"
    Restart-ForUpgrade 'Prerequisite cumulative update staged'
}
# Official Microsoft CDN downloads, pinned to the hashes in their distribution filenames.
# MSU metadata is still validated by Windows servicing when the package is installed.
$Packages = @{
    '25H2' = @{
        'x64' = @{ Hash='a0c1638cbcf4cf33dbe9a5bef69db374b4786974'; Url='https://catalog.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/fa84cc49-18b2-4c26-b389-90c96e6ae0d2/public/windows11.0-kb5054156-x64_a0c1638cbcf4cf33dbe9a5bef69db374b4786974.msu'; KB='KB5054156' }
        'arm64' = @{ Hash='3d5c91aaeb08a87e0717f263ad4a61186746e465'; Url='https://catalog.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/78b265e5-83a8-4e0a-9060-efbe0bac5bde/public/windows11.0-kb5054156-arm64_3d5c91aaeb08a87e0717f263ad4a61186746e465.msu'; KB='KB5054156' }
    }
    '26H2' = @{
        'x64' = @{ Hash='5e20a3cce48d6611b16bdec42b07167f5456586a'; Url='https://catalog.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/94520a88-858f-4832-a57d-7211f6d84a4e/public/Windows11.0-KB5121794-x64_5e20a3cce48d6611b16bdec42b07167f5456586a.msu'; KB='KB5121794' }
        'arm64' = @{ Hash='77a76caf2d362bb293a4d18058388f2717365abe'; Url='https://catalog.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/9d8dc3d0-9cbf-4eb1-9411-722e3e6a19b3/public/Windows11.0-KB5121794-arm64_77a76caf2d362bb293a4d18058388f2717365abe.msu'; KB='KB5121794' }
    }
}
function Install-Enablement([string]$Target, [string]$Arch) {
    $p = $Packages[$Target][$Arch]
    $path = Join-Path $Root ("{0}_{1}.msu" -f $p.KB,$Arch)
    $needDownload = $true
    if (Test-Path -LiteralPath $path) {
        $old = (Get-FileHash -LiteralPath $path -Algorithm SHA1).Hash.ToLowerInvariant()
        $needDownload = ($old -ne $p.Hash)
        if ($needDownload) { Remove-Item -LiteralPath $path -Force }
    }
    if ($needDownload) {
        State 'DOWNLOADING' "Downloading $Target enablement package ($($p.KB)) from Microsoft CDN to D:."
        $temp = "$path.download"
        if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Force }
        Invoke-WebRequest -Uri $p.Url -OutFile $temp -UseBasicParsing -TimeoutSec 120
        if ((Get-Item -LiteralPath $temp).Length -lt 50000) { throw 'Downloaded file is too small to be the expected MSU.' }
        $hash = (Get-FileHash -LiteralPath $temp -Algorithm SHA1).Hash.ToLowerInvariant()
        if ($hash -ne $p.Hash) {
            Remove-Item -LiteralPath $temp -Force
            throw "MSU integrity mismatch. Expected=$($p.Hash); got=$hash. Aborted."
        }
        Move-Item -LiteralPath $temp -Destination $path -Force
    }
    State 'INSTALLING' "Installing $Target $($p.KB) from $path via WUSA (no ISO)."
    $wusa = Join-Path $env:SystemRoot 'System32\wusa.exe'
    $proc = Start-Process -FilePath $wusa -ArgumentList @('"'+$path+'"','/quiet','/norestart') -PassThru -Wait
    $exit = [long]$proc.ExitCode
    if ($exit -lt 0) { $exit += 4294967296 }
    Log ('WUSA exit code: 0x{0:X8} ({1})' -f $exit,$exit)
    if ($exit -notin @(0,3010,2359302)) {
        throw ('WUSA refused/failure (0x{0:X8}). Confirm 24H2 build prerequisites and CBS logs.' -f $exit)
    }
    Restart-ForUpgrade "$Target $($p.KB) staged"
}

try {
    $os = Get-OSInfo
    Log "Start computer=$env:COMPUTERNAME; user=$([Security.Principal.WindowsIdentity]::GetCurrent().Name); version=$($os.Version); build=$($os.Build).$($os.UBR); resume=$Resume"
    if ($os.Build -eq 26300 -or $os.Build -eq 26200) {
        State 'SUCCESS' "Windows 11 $($os.Version) installed (OS build $($os.Build).$($os.UBR))."
        Unschedule-Continue
        if (Test-Path -LiteralPath $RebootCountFile) { Remove-Item -LiteralPath $RebootCountFile -Force }
        exit 0
    }
    if ($VerifyOnly) {
        State 'NOT_COMPLETE' "Windows has not reached 25H2; current build $($os.Build).$($os.UBR)."
        exit 2
    }
    if ($os.Build -ne 26100) { throw "This script only upgrades Windows 11 24H2 (26100.x). Actual: $($os.Build).$($os.UBR)." }
    if ($os.Edition -match '(?i)EnterpriseS|IoTEnterpriseS') { throw "LTSC edition $($os.Edition) is not supported by these enablement packages." }
    $arch = if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() -eq 'Arm64') { 'arm64' } else { 'x64' }
    if ($env:PROCESSOR_ARCHITECTURE -eq 'x86') { throw 'Run 64-bit PowerShell, not 32-bit PowerShell.' }
    if (Is-RebootPending) {
        Restart-ForUpgrade 'Existing Windows servicing requires a reboot before applying enablement package'
        exit 0
    }
    if ($os.UBR -lt $Min25UBR) {
        Install-Required-LCU
        exit 0
    }
    $target = if (-not $Prefer25H2 -and $os.UBR -ge $Min26UBR) { '26H2' } else { '25H2' }
    Log "Target=$target. Current 24H2 UBR=$($os.UBR), minimum 25H2=$Min25UBR, minimum 26H2=$Min26UBR."
    if ($target -eq '26H2') {
        try {
            Install-Enablement -Target '26H2' -Arch $arch
        }
        catch {
            Log "26H2 failed: $($_.Exception.Message)"
            if (Is-RebootPending) { throw '26H2 failed with pending servicing; cannot safely fall back before reboot.' }
            Log 'Fallback to 25H2 enablement package.'
            Install-Enablement -Target '25H2' -Arch $arch
        }
    } else {
        Install-Enablement -Target '25H2' -Arch $arch
    }
    exit 0
}
catch {
    State 'ERROR' $_.Exception.Message
    Log $_.ScriptStackTrace
    exit 1
}
