@echo off
chcp 65001 >nul
echo ============================================
echo  DesktopPet - Windows GIF桌宠 打包脚本
echo ============================================
echo.

set PYTHON="C:\Users\31960\anaconda3\python.exe"
set SCRIPT_DIR=%~dp0

echo 1. 安装依赖...
%PYTHON% -m pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 2. 安装 PyInstaller...
%PYTHON% -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo [错误] PyInstaller 安装失败
    pause
    exit /b 1
)

echo.
echo 3. 打包中...
cd /d "%SCRIPT_DIR%"
%PYTHON% -m PyInstaller --onefile --windowed --name "DesktopPet" ^
    --add-data "qinren;qinren" ^
    --add-data "assets;assets" ^
    --icon "assets/icon.ico" ^
    main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo  打包成功！
echo  输出文件: dist\DesktopPet.exe
echo ============================================
pause
