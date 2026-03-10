"""
Pipeline Module
===============
Parallel processing pipeline using DAG scheduling.

Supports both single-speaker and multi-speaker audio analysis pipelines.
"""

import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

from .logger import get_logger

logger = get_logger(__name__)


class StageStatus(Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStage:
    """A single stage in the processing pipeline."""
    name: str
    func: Callable
    dependencies: Set[str] = field(default_factory=set)
    status: StageStatus = StageStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None


class Pipeline:
    """
    DAG-based parallel processing pipeline.

    Stages are executed in parallel when their dependencies are met.
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize the pipeline.

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.stages: Dict[str, PipelineStage] = {}
        self.max_workers = max_workers
        self.executor: Optional[ThreadPoolExecutor] = None

    def add_stage(
        self,
        name: str,
        func: Callable,
        dependencies: Optional[List[str]] = None
    ) -> "Pipeline":
        """
        Add a stage to the pipeline.

        Args:
            name: Unique stage name
            func: Function to execute
            dependencies: List of stage names that must complete first

        Returns:
            Self for chaining
        """
        deps = set(dependencies) if dependencies else set()
        self.stages[name] = PipelineStage(
            name=name,
            func=func,
            dependencies=deps
        )
        logger.debug("Stage added", name=name, dependencies=list(deps))
        return self

    async def execute(self, initial_input: Any) -> Dict[str, Any]:
        """
        Execute the pipeline.

        Args:
            initial_input: Initial input data

        Returns:
            Dictionary of results keyed by stage name
        """
        logger.info("Pipeline execution started", num_stages=len(self.stages))

        # Initialize executor
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # Track running futures
        futures: Dict[str, Future] = {}
        results: Dict[str, Any] = {}

        # Initial inputs for each stage
        stage_inputs: Dict[str, Any] = {name: initial_input for name in self.stages}

        # Track completed stages
        completed: Set[str] = set()

        try:
            while len(completed) < len(self.stages):
                # Find stages ready to run
                ready_stages = [
                    name for name, stage in self.stages.items()
                    if stage.status == StageStatus.PENDING
                    and stage.dependencies.issubset(completed)
                ]

                # Submit ready stages
                for stage_name in ready_stages:
                    stage = self.stages[stage_name]
                    stage.status = StageStatus.RUNNING
                    logger.debug("Stage started", name=stage_name)

                    # Collect dependencies' results
                    deps_results = {dep: results[dep] for dep in stage.dependencies}

                    # Prepare input: combine initial input with dependency results
                    input_data = {
                        "initial": stage_inputs[stage_name],
                        "dependencies": deps_results
                    }

                    # Submit to executor
                    future = self.executor.submit(self._run_stage, stage_name, input_data)
                    futures[stage_name] = future

                # Wait for at least one stage to complete
                if not futures:
                    if len(completed) < len(self.stages):
                        # Deadlock - stages pending but none can run
                        pending = [s for s in self.stages if s not in completed]
                        logger.error("Pipeline deadlock", pending=pending)
                        raise RuntimeError(f"Pipeline deadlock: stages {pending} cannot run")
                    break

                # Wait for any future to complete
                done, _ = await asyncio.wait(
                    futures.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed futures
                for future in done:
                    # Find the stage name
                    stage_name = None
                    for name, f in futures.items():
                        if f == future:
                            stage_name = name
                            break

                    if stage_name is None:
                        continue

                    stage = self.stages[stage_name]
                    del futures[stage_name]

                    try:
                        result = future.result()
                        stage.status = StageStatus.COMPLETED
                        stage.result = result
                        results[stage_name] = result
                        completed.add(stage_name)
                        logger.debug("Stage completed", name=stage_name)

                        # Update input for dependent stages
                        for other_name, other_stage in self.stages.items():
                            if stage_name in other_stage.dependencies:
                                stage_inputs[other_name] = {
                                    "initial": stage_inputs[other_name],
                                    "dependencies": results.copy()
                                }

                    except Exception as e:
                        stage.status = StageStatus.FAILED
                        stage.error = e
                        logger.error("Stage failed", name=stage_name, error=str(e))
                        raise

            logger.info("Pipeline execution completed", num_stages=len(self.stages))
            return results

        finally:
            self.executor.shutdown(wait=True)
            self.executor = None

    def _run_stage(self, stage_name: str, input_data: Dict[str, Any]) -> Any:
        """
        Run a single stage.

        Args:
            stage_name: Name of the stage
            input_data: Input data dict

        Returns:
            Stage result
        """
        stage = self.stages[stage_name]

        # Prepare kwargs
        kwargs = {}
        if isinstance(input_data, dict):
            # If dependencies exist, pass them
            if "dependencies" in input_data and input_data["dependencies"]:
                kwargs["dependency_results"] = input_data["dependencies"]
            # Pass initial input
            if "initial" in input_data:
                kwargs["input"] = input_data["initial"]
            elif input_data:
                kwargs["input"] = input_data

        try:
            return stage.func(**kwargs)
        except Exception as e:
            logger.error("Stage execution error", stage=stage_name, error=str(e))
            raise


class AudioAnalysisPipeline:
    """
    Pre-configured pipeline for audio analysis.

    Stage dependencies:
    - Stage 1 (parallel): AudioLoader, VAD, STT
    - Stage 2 (parallel): ProsodyAnalyzer, FillerDetector (depend on STT)
    - Stage 3: MetricsBuilder (depends on all)
    """

    @staticmethod
    def create_pipeline(
        audio_file: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Pipeline:
        """
        Create an audio analysis pipeline.

        Args:
            audio_file: Path to audio file
            config: Optional configuration

        Returns:
            Configured Pipeline instance
        """
        from modules.audio_loader import AudioLoader
        from modules.vad_analyzer import VADAnalyzer
        from modules.speech_to_text import SpeechToText
        from modules.prosody_analyzer import ProsodyAnalyzer
        from modules.filler_detector import FillerDetector
        from modules.metrics_builder import MetricsBuilder

        config = config or {}

        pipeline = Pipeline(max_workers=config.get("max_workers", 4))

        # Stage 1: Load audio (no dependencies)
        def load_audio(input: str) -> Dict[str, Any]:
            loader = AudioLoader(input)
            loader.load()
            loader.validate(max_duration=config.get("max_duration", 3600))
            return {
                "audio_data": loader.get_audio_data(),
                "audio_info": loader.get_audio_info(),
                "file_path": input
            }

        pipeline.add_stage("load_audio", load_audio, dependencies=[])

        # Stage 2: VAD analysis (depends on load_audio)
        def run_vad(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            vad = VADAnalyzer()
            return vad.analyze(input["audio_data"])

        pipeline.add_stage("vad", run_vad, dependencies=["load_audio"])

        # Stage 3: Speech to text (depends on load_audio)
        def run_stt(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            stt = SpeechToText(model_name=config.get("stt_model", "base"))
            return stt.transcribe(input["file_path"])

        pipeline.add_stage("stt", run_stt, dependencies=["load_audio"])

        # Stage 4: Prosody analysis (depends on load_audio)
        def run_prosody(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            audio_info = input["audio_info"]
            prosody = ProsodyAnalyzer(sample_rate=audio_info["sample_rate"])
            return prosody.analyze(input["audio_data"])

        pipeline.add_stage("prosody", run_prosody, dependencies=["load_audio"])

        # Stage 5: Filler detection (depends on STT)
        def run_filler(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            transcript = dependency_results.get("stt", {})
            filler = FillerDetector(language=transcript.get("language", "en"))
            return filler.detect(transcript.get("text", ""))

        pipeline.add_stage("filler", run_filler, dependencies=["stt"])

        # Stage 6: Build metrics (depends on all)
        def build_metrics(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            builder = MetricsBuilder()
            return builder.build(
                audio_info=dependency_results["load_audio"]["audio_info"],
                vad_analysis=dependency_results["vad"],
                transcript_result=dependency_results["stt"],
                prosody_metrics=dependency_results["prosody"],
                emotion_metrics={"dominant_emotion": "neutral", "confidence": 0.5},
                filler_metrics=dependency_results["filler"]
            )

        pipeline.add_stage("metrics", build_metrics, dependencies=["vad", "stt", "prosody", "filler"])

        return pipeline


async def run_parallel_analysis(
    audio_file: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run audio analysis with parallel processing.

    Args:
        audio_file: Path to audio file
        config: Optional configuration

    Returns:
        Analysis results
    """
    pipeline = AudioAnalysisPipeline.create_pipeline(audio_file, config)
    results = await pipeline.execute(audio_file)
    return results.get("metrics", {})


class MultiSpeakerPipeline:
    """
    Pre-configured pipeline for multi-speaker conversation analysis.
    
    Stage flow:
    1. Load audio
    2. VAD analysis
    3. Speaker diarization
    4. Build timeline
    5. Extract segment metrics
    6. Compute timing relations
    7. Aggregate speaker metrics
    8. Export results
    """
    
    @staticmethod
    def create_pipeline(
        audio_file: str,
        num_speakers: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Pipeline:
        """
        Create a multi-speaker analysis pipeline.
        
        Args:
            audio_file: Path to audio file
            num_speakers: Number of speakers (if known)
            config: Optional configuration
            
        Returns:
            Configured Pipeline instance
        """
        from modules.audio_loader import AudioLoader
        from modules.vad_analyzer import VADAnalyzer
        from modules.speaker_diarization import SpeakerDiarization
        from modules.timeline_builder import TimelineBuilder
        from modules.segment_metrics import SegmentMetricsExtractor
        from modules.speaker_metrics import SpeakerMetricsAggregator
        from modules.timing_relation import TimingRelationAnalyzer
        
        config = config or {}
        pipeline = Pipeline(max_workers=config.get("max_workers", 4))
        
        # Stage 1: Load audio
        def load_audio(input: str) -> Dict[str, Any]:
            loader = AudioLoader(input)
            loader.load()
            loader.validate(max_duration=config.get("max_duration", 3600))
            return {
                "audio_data": loader.get_audio_data(),
                "audio_info": loader.get_audio_info(),
                "file_path": input
            }
        
        pipeline.add_stage("load_audio", load_audio, dependencies=[])
        
        # Stage 2: VAD analysis
        def run_vad(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            vad = VADAnalyzer()
            return vad.analyze(input["audio_data"], input["audio_info"]["sample_rate"])
        
        pipeline.add_stage("vad", run_vad, dependencies=["load_audio"])
        
        # Stage 3: Speaker diarization
        def run_diarization(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            diarizer = SpeakerDiarization()
            return diarizer.diarize(
                input["file_path"],
                num_speakers=num_speakers
            )
        
        pipeline.add_stage("diarization", run_diarization, dependencies=["load_audio"])
        
        # Stage 4: Build timeline
        def build_timeline(input: Dict[str, Any], dependency_results: Dict) -> List[Dict]:
            builder = TimelineBuilder()
            return builder.build(
                diarization_segments=dependency_results["diarization"]["segments"],
                vad_segments=dependency_results["vad"].get("speech_segments", []),
                audio_duration=input["audio_info"]["duration_seconds"]
            )
        
        pipeline.add_stage("timeline", build_timeline, dependencies=["vad", "diarization"])
        
        # Stage 5: Extract segment metrics
        def extract_segment_metrics(input: Dict[str, Any], dependency_results: Dict) -> List[Dict]:
            extractor = SegmentMetricsExtractor(
                sample_rate=input["audio_info"]["sample_rate"]
            )
            return extractor.extract(
                input["audio_data"],
                dependency_results["diarization"]["segments"]
            )
        
        pipeline.add_stage("segment_metrics", extract_segment_metrics, dependencies=["load_audio", "diarization"])
        
        # Stage 6: Compute timing relations
        def compute_timing(input: Dict[str, Any], dependency_results: Dict) -> Dict:
            analyzer = TimingRelationAnalyzer()
            return analyzer.analyze(dependency_results["timeline"])
        
        pipeline.add_stage("timing", compute_timing, dependencies=["timeline"])
        
        # Stage 7: Aggregate speaker metrics
        def aggregate_speaker_metrics(input: Dict[str, Any], dependency_results: Dict) -> List[Dict]:
            aggregator = SpeakerMetricsAggregator()
            profiles = aggregator.aggregate(
                dependency_results["timeline"],
                dependency_results["segment_metrics"]
            )
            return aggregator.compute_conversation_roles(profiles)
        
        pipeline.add_stage("speaker_metrics", aggregate_speaker_metrics, dependencies=["timeline", "segment_metrics"])
        
        return pipeline


async def run_multi_speaker_analysis(
    audio_file: str,
    num_speakers: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run multi-speaker conversation analysis.
    
    Args:
        audio_file: Path to audio file
        num_speakers: Number of speakers (if known)
        config: Optional configuration
        
    Returns:
        Multi-speaker analysis results
    """
    pipeline = MultiSpeakerPipeline.create_pipeline(audio_file, num_speakers, config)
    results = await pipeline.execute(audio_file)
    
    # Aggregate results into final structure
    return {
        "audio_info": results["load_audio"]["audio_info"],
        "conversation_timeline": results["timeline"],
        "speaker_profiles": results["speaker_metrics"],
        "conversation_metrics": {
            "num_speakers": results["diarization"]["num_speakers"],
            "timing": results["timing"]
        },
        "segment_acoustic_metrics": results["segment_metrics"]
    }
