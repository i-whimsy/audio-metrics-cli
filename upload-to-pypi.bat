@echo off
chcp 65001 >nul
echo ==============================================
echo 🚀 Upload audio-metrics-cli to PyPI
echo ==============================================
echo.

REM Check if dist files exist
if not exist "dist\*.whl" (
    echo ❌ No distribution files found!
    echo Please run: python -m build
    pause
    exit /b 1
)

echo 📦 Found distribution files:
dir /b dist\*.whl dist\*.tar.gz
echo.

echo 🔑 Please enter your PyPI API token:
echo (Username will be: __token__)
echo.

REM Upload to PyPI
echo 📤 Uploading to PyPI...
python -m twine upload dist/* -u __token__ -p %PYPI_TOKEN%

if %errorlevel% equ 0 (
    echo.
    echo ==============================================
    echo ✅ Upload successful!
    echo ==============================================
    echo.
    echo 🔗 PyPI page: https://pypi.org/project/audio-metrics-cli/
    echo.
    echo 💡 Install with: pip install audio-metrics-cli
    echo.
) else (
    echo.
    echo ==============================================
    echo ❌ Upload failed!
    echo ==============================================
    echo.
    echo 💡 Make sure:
    echo    1. You have a valid PyPI API token
    echo    2. Set PYPI_TOKEN environment variable
    echo    3. Token has upload permissions
    echo.
)

pause
