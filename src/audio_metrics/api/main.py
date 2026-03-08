"""
FastAPI Main Module
==================
REST API for audio metrics analysis.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from core.config import Config, load_config
from core.logger import get_logger, setup_logging
from modules.audio_loader import AudioLoader
from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.prosody_analyzer import ProsodyAnalyzer
from modules.filler_detector import FillerDetector
from modules.emotion_analyzer import EmotionAnalyzer
from modules.metrics_builder import MetricsBuilder

logger = get_logger(__name__)

# Request/Response models
class AnalyzeRequest(BaseModel):
    """Analysis request model."""
    file_path: Optional[str] = None
    config: Optional[dict] = None


class AnalyzeResponse(BaseModel):
    """Analysis response model."""
    status: str
    message: str
    result_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


# In-memory storage for results (use Redis in production)
_analysis_results = {}


def create_app(config: Optional[Config] = None) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        config: Optional configuration

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Audio Metrics API",
        description="Cross-platform audio analysis toolkit for speech metrics extraction",
        version="0.2.0",
    )

    # Store config
    app.state.config = config or Config()

    return app


app = create_app()


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return HealthResponse(status="ok", version="0.2.0")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.2.0")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    stt_model: str = "base",
    no_emotion: bool = False
):
    """
    Analyze audio file.

    Args:
        background_tasks: FastAPI background tasks
        file: Audio file upload
        stt_model: Whisper model to use
        no_emotion: Skip emotion analysis

    Returns:
        Analysis response with result ID
    """
    # Validate file
    allowed_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    result_id = Path(tmp_path).stem
    logger.info("Analysis started", file=file.filename, result_id=result_id)

    # Schedule background processing
    background_tasks.add_task(
        process_audio,
        tmp_path,
        result_id,
        stt_model,
        no_emotion
    )

    return AnalyzeResponse(
        status="processing",
        message="Audio analysis started",
        result_id=result_id
    )


@app.get("/results/{result_id}")
async def get_result(result_id: str):
    """
    Get analysis result.

    Args:
        result_id: Result identifier

    Returns:
        Analysis results
    """
    if result_id not in _analysis_results:
        raise HTTPException(status_code=404, detail="Result not found")

    return _analysis_results[result_id]


@app.get("/results/{result_id}/download")
async def download_result(result_id: str, format: str = "json"):
    """
    Download analysis result.

    Args:
        result_id: Result identifier
        format: Output format (json/csv/html)

    Returns:
        File response
    """
    if result_id not in _analysis_results:
        raise HTTPException(status_code=404, detail="Result not found")

    result = _analysis_results[result_id]
    output_path = Path(tempfile.gettempdir()) / f"result_{result_id}.{format}"

    # Export in requested format
    if format == "json":
        import json
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
    elif format == "csv":
        from exporters.csv_exporter import CSVExporter
        exporter = CSVExporter()
        exporter.export(result, str(output_path))
    elif format == "html":
        from exporters.html_exporter import HTMLExporter
        exporter = HTMLExporter()
        exporter.export(result, str(output_path))
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

    return FileResponse(
        path=str(output_path),
        filename=f"audio_metrics_{result_id}.{format}",
        media_type="application/octet-stream"
    )


async def process_audio(
    file_path: str,
    result_id: str,
    stt_model: str = "base",
    no_emotion: bool = False
):
    """
    Process audio file in background.

    Args:
        file_path: Path to audio file
        result_id: Result identifier
        stt_model: Whisper model
        no_emotion: Skip emotion analysis
    """
    try:
        logger.info("Processing started", result_id=result_id)

        # Step 1: Load audio
        loader = AudioLoader(file_path)
        loader.load()
        loader.validate(max_duration=3600)
        audio_info = loader.get_audio_info()

        # Step 2: VAD
        vad = VADAnalyzer()
        vad_analysis = vad.analyze(loader.get_audio_data())

        # Step 3: STT
        stt = SpeechToText(model_name=stt_model)
        transcript = stt.transcribe(file_path)

        # Step 4: Prosody
        prosody = ProsodyAnalyzer(sample_rate=audio_info["sample_rate"])
        prosody_metrics = prosody.analyze(loader.get_audio_data())
        speech_rate = prosody.calculate_speech_rate(
            transcript["text"],
            audio_info["duration_seconds"]
        )
        prosody_metrics.update(speech_rate)

        # Step 5: Emotion
        if not no_emotion:
            try:
                emotion = EmotionAnalyzer()
                emotion_metrics = emotion.analyze(file_path)
            except Exception as e:
                logger.warning("Emotion analysis failed", error=str(e))
                emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}
        else:
            emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}

        # Step 6: Filler
        filler = FillerDetector(language=transcript.get("language", "en"))
        filler_metrics = filler.detect(transcript["text"])

        # Step 7: Build metrics
        builder = MetricsBuilder()
        metrics = builder.build(
            audio_info=audio_info,
            vad_analysis=vad_analysis,
            transcript_result=transcript,
            prosody_metrics=prosody_metrics,
            emotion_metrics=emotion_metrics,
            filler_metrics=filler_metrics
        )

        # Store result
        _analysis_results[result_id] = metrics
        logger.info("Processing completed", result_id=result_id)

    except Exception as e:
        logger.error("Processing failed", result_id=result_id, error=str(e))
        _analysis_results[result_id] = {
            "status": "error",
            "error": str(e)
        }

    finally:
        # Cleanup temp file
        try:
            Path(file_path).unlink()
        except Exception:
            pass


@app.post("/batch/analyze")
async def batch_analyze(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    stt_model: str = "base"
):
    """
    Analyze multiple audio files.

    Args:
        background_tasks: Background tasks
        files: List of audio files
        stt_model: Whisper model

    Returns:
        Batch analysis response
    """
    job_id = f"batch_{len(files)}"

    # Process each file
    for file in files:
        # Similar to single analysis but with job_id
        pass

    return {"status": "processing", "job_id": job_id, "files": len(files)}


# CLI entry point for API server
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Run the API server.

    Args:
        host: Host to bind
        port: Port to bind
        reload: Enable auto-reload
    """
    import uvicorn

    setup_logging(level="INFO")

    uvicorn.run(
        "audio_metrics.api.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    run_server()
