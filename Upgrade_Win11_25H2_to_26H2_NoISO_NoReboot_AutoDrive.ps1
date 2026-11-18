# Windows 11 25H2 -> 26H2 (KB5121794) via Microsoft-hosted enablement package
# No ISO. No automatic reboot. Run as an elevated administrator or SYSTEM.
# Work files and logs: D:\Win11Upgrade; fallback C:\Win11Upgrade.
# Prerequisite: 25H2 build 26200.9550 or later (conservative threshold).
# Source: https://support.microsoft.com/en-us/servicing/os/windows-11/2026/09/kb5121794-feature-update-to-windows-11-version-26h2

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$rootDrive = if (Test-Path -LiteralPath 'D:\') { 'D:' } else { 'C:' }
$Root = Join-Path ($rootDrive + '\') 'Win11Upgrade'
$LogDir = Join-Path $Root 'Logs'
$LogFile = Join-Path $LogDir '25H2_to_26H2.log'
$StatusFile = Join-Path $Root '25H2_to_26H2_status.json'
$Package = Join-Path $Root 'Windows11.0-KB5121794-x64.msu'
$TempPackage = "$Package.download"

# Official Microsoft CDN URL, independently cross-reference the update ID and host.
# This URL is a specific published package revision; Microsoft may retire it.
$PackageUrl = 'https://catalog.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/ad9dbefc-fd26-4e9f-80cf-16743b6c4faa/public/Windows11.0-KB5121794-x64_870a6b16d4e0e0eeeaa02b5306df5b4ecb39f563.msu'
$ExpectedSHA1 = '870a6b16d4e0e0eeeaa02b5306df5b4ecb39f563'
$MinUBR = 9550

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Log([string]$Message) {
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Message
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function CurrentOS {
    $p = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    return [PSCustomObject]@{
        Version = [string]$p.DisplayVersion
        Build = [int]$p.CurrentBuild
        UBR = [int]$p.UBR
    }
}

function Status([string]$State, [string]$Message) {
    $os = CurrentOS
    $obj = [ordered]@{
        time = (Get-Date).ToString('o')
        computer = $env:COMPUTERNAME
        state = $State
        message = $Message
        version = $os.Version
        build = $os.Build
        ubr = $os.UBR
        target = '26H2'
        kb = 'KB5121794'
        restart_automatically = $false
        work_dir = $Root
    }
    $json = $obj | ConvertTo-Json -Depth 3
    [System.IO.File]::WriteAllText($StatusFile, $json, (New-Object System.Text.UTF8Encoding($false)))
    Log "STATE=$State | $Message"
}

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Administrator or SYSTEM privileges required.'
    }

    $os = CurrentOS
    Log "Start computer=$env:COMPUTERNAME; account=$($identity.Name); Windows=$($os.Version); build=$($os.Build).$($os.UBR); path=$Root"

    if ($os.Build -ge 26300 -or $os.Version -eq '26H2') {
        Status 'ALREADY_DONE' 'Windows 11 26H2 or newer detected. No action.'
        exit 0
    }
    if ($os.Version -ne '25H2' -or $os.Build -ne 26200) {
        Status 'UNSUPPORTED' 'This script is only for Windows 11 25H2 (build 26200).'
        exit 2
    }

    $arch = (Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Architecture)
    if ([int]$arch -ne 9) {
        Status 'UNSUPPORTED_ARCH' 'This package is x64 only; ARM64 needs a different package.'
        exit 2
    }

    if ($os.UBR -lt $MinUBR) {
        Status 'PREREQUISITE_REQUIRED' "Build 26200.$($os.UBR) is too old. Install KB5124010 (or newer cumulative update) until at least 26200.$MinUBR, reboot, then run again."
        exit 2
    }

    # Avoid installing an enablement package while another update awaits reboot.
    $rebootPending = (Test-Path -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or
                     (Test-Path -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
    if ($rebootPending) {
        Status 'PENDING_REBOOT' 'Windows has a pre-existing pending update reboot. Restart during a maintenance window, then rerun.'
        exit 2
    }

    $needsDownload = $true
    if (Test-Path -LiteralPath $Package) {
        $actual = (Get-FileHash -LiteralPath $Package -Algorithm SHA1).Hash.ToLowerInvariant()
        if ($actual -eq $ExpectedSHA1) {
            Log 'Reuse previously downloaded package with matching SHA1.'
            $needsDownload = $false
        } else {
            Remove-Item -LiteralPath $Package -Force
        }
    }

    if ($needsDownload) {
        Status 'DOWNLOADING' "Downloading KB5121794 from Microsoft CDN to $Package"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $uri = [Uri]$PackageUrl
        if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'catalog.sf.dl.delivery.mp.microsoft.com') {
            throw 'Refusing download from a non-Microsoft or non-HTTPS host.'
        }
        if (Test-Path -LiteralPath $TempPackage) { Remove-Item -LiteralPath $TempPackage -Force }
        Invoke-WebRequest -Uri $PackageUrl -OutFile $TempPackage -UseBasicParsing
        $size = (Get-Item -LiteralPath $TempPackage).Length
        if ($size -lt 100000 -or $size -gt 10485760) {
            throw "Unexpected MSU package size: $size bytes."
        }
        $actual = (Get-FileHash -LiteralPath $TempPackage -Algorithm SHA1).Hash.ToLowerInvariant()
        if ($actual -ne $ExpectedSHA1) {
            throw "Downloaded package hash mismatch. Expected $ExpectedSHA1, got $actual. Not installing."
        }
        Move-Item -LiteralPath $TempPackage -Destination $Package -Force
        Log "Package verified: $size bytes; SHA1=$actual"
    }

    Status 'INSTALLING' 'Installing KB5121794 silently with WUSA /quiet /norestart.'
    $proc = Start-Process -FilePath "$env:windir\system32\wusa.exe" -ArgumentList ('"{0}" /quiet /norestart' -f $Package) -Wait -PassThru
    $exitCode = [int32]$proc.ExitCode
    $hex = [BitConverter]::ToUInt32([BitConverter]::GetBytes($exitCode), 0).ToString('X8')
    Log "WUSA exit code: 0x$hex ($exitCode)"

    if ($exitCode -eq 0 -or $exitCode -eq 3010) {
        Status 'RESTART_REQUIRED' 'KB5121794 processed. No automatic restart was scheduled by this script. Restart manually and verify 26H2 (build 26300).'
        exit 0
    }
    if ($exitCode -eq 2359302) {
        Status 'ALREADY_INSTALLED_OR_NOT_APPLICABLE' 'WUSA reports update already installed or not applicable; verify the OS build and CBS logs.'
        exit 2
    }
    throw "WUSA failed with exit code 0x$hex ($exitCode). Check WindowsUpdate/CBS logs."
}
catch {
    Status 'ERROR' $_.Exception.Message
    exit 1
}
