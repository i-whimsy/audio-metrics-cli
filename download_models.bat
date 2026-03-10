@echo off
chcp 65001 >nul
echo ============================================================
echo Audio Metrics CLI - 模型一键下载脚本
echo ============================================================
echo.
echo 正在设置国内镜像加速...
set HF_ENDPOINT=https://hf-mirror.com

echo.
echo [1/5] 安装必要工具...
pip install huggingface-hub openai-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] 安装失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo [2/5] 下载 Silero VAD 模型...
cd /d C:\Users\clawbot\.cache\torch\hub
if exist silero-vad_master rmdir /s /q silero-vad_master
git clone https://ghproxy.com/https://github.com/snakers4/silero-vad.git silero-vad_master
if errorlevel 1 (
    echo [警告] Silero VAD 下载失败，可手动重试
)

echo.
echo [3/5] 下载 PyAnnotate 模型（约 400MB，请耐心等待）...
huggingface-cli download pyannote/speaker-diarization-3.1 --local-dir "C:\Users\clawbot\.cache\huggingface\hub\models--pyannote--speaker-diarization-3.1"
if errorlevel 1 (
    echo [警告] PyAnnotate 下载失败，可手动重试
)

echo.
echo [4/5] 下载 Whisper 模型...
python -c "import whisper; print('下载 base 模型...'); whisper.load_model('base'); print('完成！')"
if errorlevel 1 (
    echo [警告] Whisper 下载失败，可手动重试
)

echo.
echo [5/5] 验证安装...
cd /d C:\Users\clawbot\.openclaw\workspace\projects\audio-metrics-cli
python CHECK_DEPENDENCIES.py

echo.
echo ============================================================
echo 下载完成！
echo ============================================================
echo.
echo 模型存储位置:
echo - Silero VAD: C:\Users\clawbot\.cache\torch\hub\silero-vad_master
echo - PyAnnotate: C:\Users\clawbot\.cache\huggingface\hub\
echo - Whisper: C:\Users\clawbot\.cache\whisper\
echo.
pause
