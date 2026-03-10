@echo off
chcp 65001 >nul
echo ============================================================
echo Audio Metrics CLI - 项目清理脚本
echo ============================================================
echo.

cd /d C:\Users\clawbot\.openclaw\workspace\projects\audio-metrics-cli

echo [1/6] 删除临时 Python 脚本...
del /Q analyze_*.py 2>nul
del /Q copy_file.py 2>nul
del /Q find_file.py 2>nul
del /Q run_test.py 2>nul
del /Q test_*.py 2>nul
del /Q install_pyannote.py 2>nul
del /Q CHECK_DEPENDENCIES.py 2>nul
echo 完成

echo.
echo [2/6] 删除临时文档...
del /Q DOWNLOAD_*.md 2>nul
del /Q README_DOWNLOAD.md 2>nul
del /Q *_STATUS*.md 2>nul
del /Q PYANNOTATE_ALTERNATIVE.md 2>nul
del /Q COPY_MODELS_FROM_OTHER_PC.md 2>nul
del /Q HOW_TO_PUBLISH.md 2>nul
del /Q CLEANUP_GUIDE.md 2>nul
echo 完成

echo.
echo [3/6] 删除测试数据...
del /Q test_audio.m4a 2>nul
echo 完成

echo.
echo [4/6] 删除构建产物...
rmdir /S /Q dist 2>nul
rmdir /S /Q src\audio_metrics_cli.egg-info 2>nul
echo 完成

echo.
echo [5/6] 删除 Python 缓存...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo 完成

echo.
echo [6/6] 整理 outputs 目录...
if not exist outputs mkdir outputs
echo 完成

echo.
echo ============================================================
echo 清理完成！
echo ============================================================
echo.
echo 保留的核心文件:
echo - pyproject.toml
echo - requirements.txt
echo - README.md
echo - LICENSE
echo - .gitignore
echo - release.sh
echo - upload-to-pypi.bat
echo.
echo 保留的文档:
echo - QUICK_REFERENCE.md
echo - VOICE_ACOUSTIC_ANALYZER.md
echo - MULTI_SPEAKER_GUIDE.md
echo - REFACTOR_SUMMARY.md
echo - UPGRADE_SUMMARY.md
echo.
echo 保留的源码:
echo - src/audio_metrics/
echo   - cli.py (主入口)
echo   - core/ (核心模块)
echo   - modules/ (功能模块)
echo   - exporters/ (导出器)
echo.
pause
