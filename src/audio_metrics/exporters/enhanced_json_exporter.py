"""
Enhanced JSON Exporter
Exports rich, structured JSON with segments, speakers, topics, and summary
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from core.logger import get_logger

logger = get_logger(__name__)


class EnhancedJSONExporter:
    """Export analysis results as enriched JSON"""
    
    def __init__(self, output_path: str = None):
        """
        Initialize exporter
        
        Args:
            output_path: Output file path
        """
        self.output_path = output_path
    
    def export(
        self,
        audio_info: Dict,
        vad_analysis: Dict,
        transcript_result: Dict,
        prosody_metrics: Dict,
        emotion_metrics: Dict,
        filler_metrics: Dict,
        diarization_result: Dict = None,
        segments: List[Dict] = None,
        summary: Dict = None,
        keywords: Dict = None,
        output_path: str = None
    ) -> str:
        """
        Export enriched JSON
        
        Args:
            audio_info: Audio metadata
            vad_analysis: VAD analysis results
            transcript_result: Speech-to-text results
            prosody_metrics: Prosody analysis
            emotion_metrics: Emotion analysis
            filler_metrics: Filler word detection
            diarization_result: Speaker diarization (optional)
            segments: Segmented transcript with timestamps
            summary: One-liner summary
            keywords: Keywords and topics
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        output_path = output_path or self.output_path
        
        # Build enhanced structure
        result = self._build_enhanced_structure(
            audio_info=audio_info,
            vad_analysis=vad_analysis,
            transcript_result=transcript_result,
            prosody_metrics=prosody_metrics,
            emotion_metrics=emotion_metrics,
            filler_metrics=filler_metrics,
            diarization_result=diarization_result,
            segments=segments,
            summary=summary,
            keywords=keywords
        )
        
        # Write to file
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhanced JSON exported", path=str(output_file))
            return str(output_file)
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    def _build_enhanced_structure(
        self,
        audio_info: Dict,
        vad_analysis: Dict,
        transcript_result: Dict,
        prosody_metrics: Dict,
        emotion_metrics: Dict,
        filler_metrics: Dict,
        diarization_result: Dict = None,
        segments: List[Dict] = None,
        summary: Dict = None,
        keywords: Dict = None
    ) -> Dict[str, Any]:
        """Build the enhanced JSON structure"""
        
        # Meta section
        meta = {
            "version": "2.0.0",
            "analyzer": "audio-metrics-cli",
            "timestamp": datetime.now().isoformat(),
            "file": audio_info.get("file_name", ""),
            "duration_seconds": audio_info.get("duration_seconds", 0)
        }
        
        # Summary section
        summary_section = self._build_summary_section(
            vad_analysis=vad_analysis,
            transcript_result=transcript_result,
            diarization_result=diarization_result,
            summary=summary,
            keywords=keywords
        )
        
        # Speakers section (if diarization available)
        speakers_section = self._build_speakers_section(diarization_result, vad_analysis)
        
        # Segments section (detailed transcript with timestamps)
        segments_section = segments or self._build_simple_segments(transcript_result)
        
        # Topics section
        topics_section = self._build_topics_section(keywords)
        
        # Metrics section (all technical metrics)
        metrics_section = {
            "vad": vad_analysis,
            "prosody": prosody_metrics,
            "emotion": emotion_metrics,
            "filler_words": filler_metrics
        }
        
        # Transcript (full text, for backward compatibility)
        transcript_section = {
            "full_text": transcript_result.get("text", ""),
            "language": transcript_result.get("language", "unknown"),
            "model": transcript_result.get("model", "")
        }
        
        return {
            "meta": meta,
            "summary": summary_section,
            "speakers": speakers_section,
            "segments": segments_section,
            "topics": topics_section,
            "transcript": transcript_section,
            "metrics": metrics_section
        }
    
    def _build_summary_section(
        self,
        vad_analysis: Dict,
        transcript_result: Dict,
        diarization_result: Dict = None,
        summary: Dict = None,
        keywords: Dict = None
    ) -> Dict[str, Any]:
        """Build summary section"""
        
        # Auto-generate summary if not provided
        if not summary:
            summary = {
                "one_liner": "",
                "method": "none",
                "confidence": 0.0
            }
        
        # Calculate basic stats
        speech_ratio = vad_analysis.get("speech_ratio", 0)
        num_speakers = diarization_result.get("num_speakers", 1) if diarization_result else 1
        
        # Build key topics list
        key_topics = []
        if keywords and "topics" in keywords:
            key_topics = [t["topic"] for t in keywords["topics"][:5]]
        
        return {
            "one_liner": summary.get("one_liner", ""),
            "method": summary.get("method", "none"),
            "confidence": summary.get("confidence", 0.0),
            "stats": {
                "speech_ratio": round(speech_ratio, 3),
                "num_speakers": num_speakers,
                "total_words": len(transcript_result.get("text", "")),
                "duration_seconds": round(vad_analysis.get("speech_duration", 0), 1)
            },
            "key_topics": key_topics,
            "action_items": keywords.get("action_items", []) if keywords else []
        }
    
    def _build_speakers_section(
        self,
        diarization_result: Dict = None,
        vad_analysis: Dict = None
    ) -> Dict[str, Any]:
        """Build speakers section with VAD filtering"""
        
        if not diarization_result:
            return {
                "detected": False,
                "num_speakers": 0,
                "profiles": []
            }
        
        num_speakers = diarization_result.get("num_speakers", 0)
        segments = diarization_result.get("segments", [])
        
        # Get VAD speech segments for filtering
        vad_speech_duration = vad_analysis.get("speech_duration", 0) if vad_analysis else 0
        
        # Calculate speaker profiles (only count segments that overlap with VAD speech)
        speaker_stats = {}
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            seg_duration = seg.get("duration", 0)
            
            # Check if segment overlaps with VAD speech
            # Simple heuristic: if segment is very short (<0.5s), likely not speech
            is_speech = seg_duration >= 0.5
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "total_time": 0,
                    "turn_count": 0,
                    "speech_turns": 0
                }
            
            # Always count turns
            speaker_stats[speaker]["turn_count"] += 1
            
            # Only count speech turns
            if is_speech:
                speaker_stats[speaker]["total_time"] += seg_duration
                speaker_stats[speaker]["speech_turns"] += 1
        
        # Build profiles
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
        
        # Sort by total speech time
        profiles.sort(key=lambda x: x["total_time"], reverse=True)
        
        return {
            "detected": True,
            "num_speakers": num_speakers,
            "total_speech_duration": round(total_speech_time, 2),
            "profiles": profiles
        }
    
    def _build_simple_segments(self, transcript_result: Dict) -> List[Dict]:
        """Build simple segments when no diarization available"""
        text = transcript_result.get("text", "")
        
        # Split into rough sentences
        sentences = []
        for sep in ["。", "！", "？", "\n"]:
            text = text.replace(sep, sep + "|")
        parts = [p.strip() for p in text.split("|") if p.strip()]
        
        # Create pseudo-segments
        duration_per_char = 0.1  # Rough estimate
        current_time = 0
        
        segments = []
        for i, part in enumerate(parts[:50]):  # Limit to 50 segments
            segments.append({
                "start": round(current_time, 2),
                "end": round(current_time + len(part) * duration_per_char, 2),
                "speaker": "SPEAKER_00",
                "text": part,
                "emotion": "neutral"
            })
            current_time += len(part) * duration_per_char + 0.5
        
        return segments
    
    def _build_topics_section(self, keywords: Dict = None) -> Dict[str, Any]:
        """Build topics section"""
        
        if not keywords:
            return {
                "extracted": False,
                "keywords": [],
                "topics": []
            }
        
        return {
            "extracted": True,
            "keywords": keywords.get("keywords", [])[:10],
            "topics": keywords.get("topics", [])
        }
