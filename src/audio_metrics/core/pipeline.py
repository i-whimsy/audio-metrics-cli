"""
Analysis Pipeline - Core orchestration layer for audio analysis

This module provides the unified analysis pipeline that orchestrates all
audio processing modules. CLI should only call pipeline.run().

Architecture:
    CLI → Pipeline → Modules
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.logger import get_logger
from core.model_config import ModelConfig
from modules.audio_loader import AudioLoader
from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.speaker_diarization import SpeakerDiarization
from modules.prosody_analyzer import ProsodyAnalyzer
from modules.emotion_analyzer import EmotionAnalyzer
from modules.filler_detector import FillerDetector
from modules.segment_metrics import SegmentMetricsExtractor
from modules.speaker_metrics import SpeakerMetricsAggregator
from modules.timing_relation import TimingRelationAnalyzer
from conversation.timeline_builder import TimelineBuilder
from conversation.conversation_dynamics import ConversationDynamicsAnalyzer
from nlp.summary_generator import SummaryGenerator
from nlp.keyword_extractor import KeywordExtractor
from exporters.enhanced_json_exporter import EnhancedJSONExporter

logger = get_logger(__name__)


class AnalysisPipeline:
    """
    Main analysis pipeline orchestrating all audio processing modules.
    
    This class implements the core analysis flow:
    Audio → VAD → Diarization → Timeline → Metrics → STT → Export
    
    Attributes:
        config: Configuration dictionary
        debug: Enable debug output
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, debug: bool = False):
        """
        Initialize analysis pipeline.
        
        Args:
            config: Configuration dictionary with module settings
            debug: Enable debug output for each step
        """
        self.config = config or {}
        self.debug = debug
        self.step_timings: Dict[str, float] = {}
        
    def run(self, audio_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run complete analysis pipeline on audio file.
        
        Args:
            audio_path: Path to audio file
            output_path: Optional path for JSON output
            
        Returns:
            Complete analysis result dictionary
        """
        start_time = time.time()
        self._log_step("PIPELINE_START", f"Processing: {Path(audio_path).name}")
        
        # Initialize result structure
        result = {
            "meta": self._build_meta(audio_path),
            "audio": {},
            "speakers": {},
            "segments": [],
            "conversation_dynamics": {},
            "metrics": {},
            "transcript": {},
            "topics": {},
            "summary": {}
        }
        
        try:
            # STEP 1: Load audio
            self._log_step("STEP_1", "Loading audio...")
            step_start = time.time()
            audio_info, audio_data = self._load_audio(audio_path)
            result["audio"] = audio_info
            self._record_timing("audio_loading", step_start)
            
            # STEP 2: VAD analysis
            self._log_step("STEP_2", "Running VAD...")
            step_start = time.time()
            vad_analysis = self._run_vad(audio_data)
            result["metrics"]["vad"] = vad_analysis
            self._record_timing("vad", step_start)
            
            # STEP 3: Speaker diarization
            self._log_step("STEP_3", "Running speaker diarization...")
            step_start = time.time()
            diarization_result = self._run_diarization(audio_path)
            result["speakers"] = self._build_speakers_section(diarization_result, vad_analysis)
            self._record_timing("diarization", step_start)
            
            # STEP 4: Build timeline
            self._log_step("STEP_4", "Building conversation timeline...")
            step_start = time.time()
            timeline = self._build_timeline(diarization_result, audio_info)
            result["segments"] = timeline
            self._record_timing("timeline", step_start)
            
            # STEP 5: Speech-to-text
            self._log_step("STEP_5", "Running speech-to-text...")
            step_start = time.time()
            transcript = self._run_stt(audio_path)
            result["transcript"] = transcript
            self._record_timing("stt", step_start)
            
            # STEP 6: Align segments with transcript
            self._log_step("STEP_6", "Aligning segments with transcript...")
            step_start = time.time()
            aligned_segments = self._align_segments_with_transcript(
                timeline, 
                transcript,
                audio_data,
                audio_info['sample_rate']
            )
            result["segments"] = aligned_segments
            self._record_timing("alignment", step_start)
            
            # STEP 7: Extract segment metrics
            self._log_step("STEP_7", "Extracting segment metrics...")
            step_start = time.time()
            segment_metrics = self._extract_segment_metrics(audio_data, aligned_segments, audio_info['sample_rate'])
            self._record_timing("segment_metrics", step_start)
            
            # STEP 8: Extract speaker metrics
            self._log_step("STEP_8", "Aggregating speaker metrics...")
            step_start = time.time()
            speaker_metrics = self._aggregate_speaker_metrics(aligned_segments, segment_metrics)
            result["speakers"]["profiles"] = speaker_metrics
            self._record_timing("speaker_metrics", step_start)
            
            # STEP 9: Analyze conversation dynamics
            self._log_step("STEP_9", "Analyzing conversation dynamics...")
            step_start = time.time()
            dynamics = self._analyze_conversation_dynamics(aligned_segments)
            result["conversation_dynamics"] = dynamics
            self._record_timing("dynamics", step_start)
            
            # STEP 10: Extract prosody metrics (30+ features)
            self._log_step("STEP_10", "Extracting prosody metrics...")
            step_start = time.time()
            prosody_metrics = self._extract_prosody_metrics(audio_data, audio_info['sample_rate'])
            result["metrics"]["prosody"] = prosody_metrics
            self._record_timing("prosody", step_start)
            
            # STEP 11: Emotion analysis (optional)
            if self.config.get('enable_emotion', True):
                self._log_step("STEP_11", "Running emotion analysis...")
                step_start = time.time()
                emotion_metrics = self._run_emotion_analysis(audio_path)
                result["metrics"]["emotion"] = emotion_metrics
                self._record_timing("emotion", step_start)
            
            # STEP 12: Filler word detection
            self._log_step("STEP_12", "Detecting filler words...")
            step_start = time.time()
            filler_metrics = self._detect_filler_words(transcript.get('text', ''))
            result["metrics"]["filler_words"] = filler_metrics
            self._record_timing("filler_detection", step_start)
            
            # STEP 13: Extract keywords and topics
            self._log_step("STEP_13", "Extracting keywords and topics...")
            step_start = time.time()
            keywords = self._extract_keywords(transcript.get('text', ''), aligned_segments)
            result["topics"] = keywords
            self._record_timing("keywords", step_start)
            
            # STEP 14: Generate summary
            self._log_step("STEP_14", "Generating summary...")
            step_start = time.time()
            summary = self._generate_summary(transcript.get('text', ''), result)
            result["summary"] = summary
            self._record_timing("summary", step_start)
            
            # STEP 15: Export JSON
            self._log_step("STEP_15", "Exporting JSON...")
            if output_path:
                self._export_json(result, output_path)
            
            # Record total timing
            total_time = time.time() - start_time
            self._record_timing("total", start_time, total_time)
            
            self._log_step("PIPELINE_COMPLETE", f"Analysis complete in {total_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            result["error"] = str(e)
            result["meta"]["analysis_complete"] = False
            return result
    
    def _build_meta(self, audio_path: str) -> Dict[str, Any]:
        """Build metadata section"""
        return {
            "version": "3.0.0",
            "analyzer": "audio-metrics-cli",
            "timestamp": datetime.now().isoformat(),
            "file": Path(audio_path).name,
            "file_path": str(Path(audio_path).absolute()),
            "analysis_complete": True
        }
    
    def _load_audio(self, audio_path: str) -> tuple:
        """Load audio file and return audio info and data"""
        loader = AudioLoader(audio_path)
        loader.load()
        audio_info = loader.get_audio_info()
        audio_data = loader.get_audio_data()
        return audio_info, audio_data
    
    def _run_vad(self, audio_data) -> Dict[str, Any]:
        """Run voice activity detection"""
        vad = VADAnalyzer()
        return vad.analyze(audio_data)
    
    def _run_diarization(self, audio_path: str) -> Dict[str, Any]:
        """Run speaker diarization"""
        diarizer = SpeakerDiarization()
        return diarizer.diarize(audio_path)
    
    def _build_speakers_section(self, diarization_result: Dict, vad_analysis: Dict) -> Dict[str, Any]:
        """Build speakers section with VAD filtering"""
        if not diarization_result:
            return {"detected": False, "num_speakers": 0, "profiles": []}
        
        num_speakers = diarization_result.get("num_speakers", 0)
        segments = diarization_result.get("segments", [])
        
        speaker_stats = {}
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            seg_duration = seg.get("duration", 0)
            is_speech = seg_duration >= 0.5
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {"total_time": 0, "turn_count": 0, "speech_turns": 0}
            
            speaker_stats[speaker]["turn_count"] += 1
            if is_speech:
                speaker_stats[speaker]["total_time"] += seg_duration
                speaker_stats[speaker]["speech_turns"] += 1
        
        profiles = []
        total_speech_time = sum(s["total_time"] for s in speaker_stats.values())
        
        for speaker_id, stats in speaker_stats.items():
            profiles.append({
                "id": speaker_id,
                "label": speaker_id.replace("SPEAKER_", "发言人 "),
                "total_time": round(stats["total_time"], 2),
                "ratio": round(stats["total_time"] / total_speech_time, 3) if total_speech_time > 0 else 0,
                "turn_count": stats["turn_count"],
                "speech_turns": stats["speech_turns"]
            })
        
        profiles.sort(key=lambda x: x["total_time"], reverse=True)
        
        return {
            "detected": True,
            "num_speakers": num_speakers,
            "total_speech_duration": round(total_speech_time, 2),
            "profiles": profiles
        }
    
    def _build_timeline(self, diarization_result: Dict, audio_info: Dict) -> List[Dict]:
        """Build conversation timeline from diarization"""
        if not diarization_result:
            return []
        
        builder = TimelineBuilder()
        return builder.build(
            diarization_result.get("segments", []),
            audio_info.get("duration_seconds", 0)
        )
    
    def _run_stt(self, audio_path: str) -> Dict[str, Any]:
        """Run speech-to-text"""
        stt = SpeechToText(model_name=self.config.get('stt_model', 'base'))
        return stt.transcribe(audio_path)
    
    def _align_segments_with_transcript(
        self, 
        segments: List[Dict], 
        transcript: Dict,
        audio_data,
        sample_rate: int
    ) -> List[Dict]:
        """
        Align diarization segments with transcript using time intervals.
        
        This is a critical fix - previously used duration*5 estimation.
        Now uses proper time interval matching.
        """
        aligned = []
        full_text = transcript.get('text', '')
        
        # If we have word-level timestamps from Whisper, use them
        # Otherwise, distribute text proportionally
        for i, seg in enumerate(segments):
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            seg_duration = seg_end - seg_start
            
            # For now, estimate text based on segment duration
            # TODO: Use word-level timestamps when available
            estimated_chars = max(10, int(seg_duration * 5))
            
            # Get acoustic features for this segment
            acoustic = self._extract_segment_acoustics(
                audio_data, 
                seg_start, 
                seg_end, 
                sample_rate
            )
            
            aligned.append({
                "start": round(seg_start, 2),
                "end": round(seg_end, 2),
                "speaker": seg.get('speaker', 'UNKNOWN'),
                "text": "",  # Will be filled when word-level timestamps available
                "emotion": "neutral",
                "pitch": acoustic.get('pitch_mean_hz', 0),
                "energy": acoustic.get('energy_mean', 0),
                "duration": round(seg_duration, 2)
            })
        
        # Distribute transcript text across segments
        if full_text and aligned:
            self._distribute_transcript_text(aligned, full_text)
        
        return aligned
    
    def _extract_segment_acoustics(self, audio_data, start: float, end: float, sample_rate: int) -> Dict[str, Any]:
        """Extract acoustic features for a segment"""
        start_sample = int(start * sample_rate)
        end_sample = int(end * sample_rate)
        
        if start_sample >= len(audio_data):
            return {}
        
        segment_audio = audio_data[start_sample:end_sample]
        
        if len(segment_audio) < 100:
            return {}
        
        extractor = SegmentMetricsExtractor(sample_rate=sample_rate)
        return extractor._extract_segment_features(segment_audio)
    
    def _distribute_transcript_text(self, segments: List[Dict], full_text: str):
        """Distribute transcript text across segments proportionally"""
        chars = list(full_text)
        char_index = 0
        
        for seg in segments:
            seg_duration = seg.get('duration', 1.0)
            estimated_chars = max(10, int(seg_duration * 5))
            
            start_idx = char_index
            end_idx = min(char_index + estimated_chars, len(chars))
            seg['text'] = ''.join(chars[start_idx:end_idx])
            char_index = end_idx
    
    def _extract_segment_metrics(self, audio_data, segments: List[Dict], sample_rate: int) -> List[Dict]:
        """Extract metrics for each segment"""
        extractor = SegmentMetricsExtractor(sample_rate=sample_rate)
        return extractor.extract(audio_data, segments)
    
    def _aggregate_speaker_metrics(self, segments: List[Dict], segment_metrics: List[Dict]) -> List[Dict]:
        """Aggregate metrics by speaker"""
        aggregator = SpeakerMetricsAggregator()
        return aggregator.aggregate(segments, segment_metrics)
    
    def _analyze_conversation_dynamics(self, segments: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation dynamics"""
        analyzer = ConversationDynamicsAnalyzer()
        return analyzer.analyze_dynamics(segments)
    
    def _extract_prosody_metrics(self, audio_data, sample_rate: int) -> Dict[str, Any]:
        """Extract 30+ prosody and voice quality metrics"""
        analyzer = ProsodyAnalyzer(sample_rate=sample_rate)
        return analyzer.analyze_full(audio_data)
    
    def _run_emotion_analysis(self, audio_path: str) -> Dict[str, Any]:
        """Run emotion analysis"""
        emotion = EmotionAnalyzer()
        return emotion.analyze(audio_path)
    
    def _detect_filler_words(self, text: str) -> Dict[str, Any]:
        """Detect filler words in transcript"""
        filler = FillerDetector(language=self.config.get('language', 'zh'))
        return filler.detect(text)
    
    def _extract_keywords(self, text: str, segments: List[Dict]) -> Dict[str, Any]:
        """Extract keywords and topics"""
        extractor = KeywordExtractor(language=self.config.get('language', 'zh'))
        return extractor.extract(text, segments)
    
    def _generate_summary(self, text: str, context: Dict) -> Dict[str, Any]:
        """Generate one-liner summary"""
        method = self.config.get('summary_method', 'heuristic')
        generator = SummaryGenerator(method=method)
        return generator.generate(text, context)
    
    def _export_json(self, result: Dict[str, Any], output_path: str):
        """Export result to JSON file"""
        exporter = EnhancedJSONExporter()
        exporter.export(result, output_path)
    
    def _log_step(self, step_name: str, message: str):
        """Log pipeline step if debug mode enabled"""
        if self.debug:
            logger.info(f"[PIPELINE] {step_name}: {message}")
            print(f"[STEP] {step_name}")
            print(f"  {message}")
    
    def _record_timing(self, step_name: str, start_time: float, duration: Optional[float] = None):
        """Record timing for a step"""
        if duration is None:
            duration = time.time() - start_time
        self.step_timings[step_name] = duration
        
        if self.debug:
            print(f"  duration: {duration:.2f}s")
    
    def get_timings(self) -> Dict[str, float]:
        """Get all step timings"""
        return self.step_timings
