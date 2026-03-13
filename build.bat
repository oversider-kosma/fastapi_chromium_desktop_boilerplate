@echo off
if /i "%~1"=="clean" (
    for /f "usebackq tokens=*" %%a in (`uv run utils.py get_repacked_name`) do set "REPACKED=%%a"

    echo Cleaning up...
    if exist .nuitka_cache rd /s /q .nuitka_cache
    if exist build_assets rd /s /q build_assets
    if exist dist rd /s /q dist
    if exist "%REPACKED%" del /f /q "%REPACKED%"
    echo Done!
    exit /b
)

echo Build started at %date% %time%
setlocal enabledelayedexpansion

chcp 65001
set LANG=en_US.UTF-8
set LC_ALL=C

set NUITKA_CACHE_DIR=.nuitka_cache

uv sync || goto :error
uv run utils.py bumb || goto :error

for /f "usebackq tokens=*" %%a in (`uv run utils.py get_version`) do set "VERSION=%%a"
for /f "usebackq tokens=*" %%a in (`uv run utils.py get_name`) do set "APPNAME=%%a"
for /f "usebackq tokens=*" %%a in (`uv run utils.py get_description`) do set "DESCRIPTION=%%a"


where ccache >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] ccache was not found in your PATH.
    echo [INFO] Nuitka builds can be significantly faster with caching enabled.
    echo [INFO] Consider installing ccache to speed up future compilations.
    echo [INFO] You can install it via: winget install ccache
    echo.
) else (
    echo [OK] ccache detected. Good. Nuitka will use it for caching.
)

uv run nuitka ^
    --standalone ^
    --onefile ^
    --product-version=%VERSION% ^
    --file-version=%VERSION% ^
    --product-name="%APPNAME%" ^
    --file-description="%DESCRIPTION%" ^
    --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" ^
    --jobs=%NUMBER_OF_PROCESSORS% ^
    --assume-yes-for-downloads ^
    --include-data-dir=frontend=frontend ^
    --include-data-dir=vendor=vendor ^
    --include-data-file=pyproject.toml=pyproject.toml ^
    --include-data-file=.build_no=.build_no ^
    --windows-console-mode=attach ^
    --onefile-windows-splash-screen-image="misc/splashscreen.png" ^
    --windows-icon-from-ico=frontend/static/favicon.ico ^
    --user-plugin=prepare_build.py ^
    --output-dir=dist ^
    --output-filename="%APPNAME%_v%VERSION%.exe" ^
    main.py

if %errorlevel% neq 0 goto :error
echo Build finished at %date% %time%
exit /b 0

:error
echo Build FAILED at %date% %time% with error %errorlevel%
exit /b %errorlevel%
