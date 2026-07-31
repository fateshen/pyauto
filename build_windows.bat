@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python 3.13 was not found.
        exit /b 1
    )
    set "PYTHON_EXE=py -3.13"
)

%PYTHON_EXE% -c "import PyInstaller"
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed in the selected Python environment.
    exit /b 1
)

%PYTHON_EXE% -m compileall -q core models ui tasks
if errorlevel 1 (
    echo [ERROR] Python source compilation failed.
    exit /b 1
)

%PYTHON_EXE% -m PyInstaller --noconfirm --clean "游戏助手.spec"
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

if not exist "dist\游戏助手\游戏助手.exe" (
    echo [ERROR] dist\游戏助手\游戏助手.exe was not created.
    exit /b 1
)

echo [OK] Windows release: dist\游戏助手
exit /b 0
