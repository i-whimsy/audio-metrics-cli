"""
JSON Exporter Module
====================
Exports analysis results to JSON with support for multi-speaker conversations.

Supports both single-speaker and multi-speaker output formats.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class JSONExporter:
    """Export analysis results to JSON with multi-speaker support."""
    
    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """
        Initialize JSON exporter.
        
        Args:
            indent: JSON indentation level
            ensure_ascii: Whether to escape non-ASCII characters
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        
    def export(
        self,
        metrics: Dict[str, Any],
        output_path: str,
        include_transcript: bool = True
    ) -> str:
        """
        Export metrics to JSON file (legacy single-speaker format).
        
        Args:
            metrics: Analysis metrics
            output_path: Output file path
            include_transcript: Whether to include full transcript
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        export_data = metrics.copy()
        
        # Optionally exclude full transcript
        if not include_transcript and "transcript" in export_data:
            export_data["transcript"] = {
                "model": metrics["transcript"].get("model", "unknown"),
                "language": metrics["transcript"].get("language", "unknown"),
                "word_count": metrics["speech_metrics"].get("words_total", 0),
                "note": "Transcript excluded from export"
            }
        
        # Write JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                export_data,
                f,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii
            )
        
        return str(output_file)
    
    def export_multi_speaker(
        self,
        audio_info: Dict[str, Any],
        conversation_timeline: List[Dict[str, Any]],
        speaker_profiles: List[Dict[str, Any]],
        conversation_metrics: Dict[str, Any],
        global_acoustic_metrics: Dict[str, Any],
        processing_meta: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Export multi-speaker analysis results.
        
        Args:
            audio_info: Audio metadata
            conversation_timeline: Timeline of conversation segments
            speaker_profiles: Speaker-level statistics
            conversation_metrics: Overall conversation metrics
            global_acoustic_metrics: Global acoustic features
            processing_meta: Processing metadata
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build result structure
        result = {
            "audio_info": audio_info,
            "conversation_timeline": conversation_timeline,
            "speaker_profiles": speaker_profiles,
            "conversation_metrics": conversation_metrics,
            "global_acoustic_metrics": global_acoustic_metrics,
            "processing_meta": processing_meta
        }
        
        # Write JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                result,
                f,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii
            )
        
        return str(output_file)
    
    def export_compact(
        self,
        metrics: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Export compact JSON (no whitespace).
        
        Args:
            metrics: Analysis metrics
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                metrics,
                f,
                separators=(',', ':'),
                ensure_ascii=self.ensure_ascii
            )
        
        return str(output_file)
    
    def export_timeline_only(
        self,
        timeline: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Export conversation timeline only.
        
        Args:
            timeline: Conversation timeline segments
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                {"conversation_timeline": timeline},
                f,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii
            )
        
        return str(output_file)
    
    def export_speaker_profiles(
        self,
        profiles: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Export speaker profiles only.
        
        Args:
            profiles: Speaker profiles
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                {"speaker_profiles": profiles},
                f,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii
            )
        
        return str(output_file)
    
    def create_report(
        self,
        metrics: Dict[str, Any],
        template: str = "default"
    ) -> str:
        """
        Create human-readable report.
        
        Args:
            metrics: Analysis metrics
            template: Report template ('default', 'detailed', 'summary')
            
        Returns:
            Report text
        """
        if template == "summary":
            return self._create_summary_report(metrics)
        elif template == "detailed":
            return self._create_detailed_report(metrics)
        else:
            return self._create_default_report(metrics)
    
    def _create_default_report(self, metrics: Dict[str, Any]) -> str:
        """Create default report."""
        # Check if multi-speaker format
        if "conversation_timeline" in metrics:
            return self._create_multi_speaker_report(metrics)
        
        # Legacy single-speaker format
        lines = [
            "=" * 60,
            "Sales Audio Analysis Report",
            "=" * 60,
            "",
            f"File: {metrics['audio_info']['file_name']}",
            f"Duration: {metrics['audio_info']['duration_seconds']:.1f}s",
            "",
            "SPEECH METRICS",
            "-" * 30,
            f"Words: {metrics['speech_metrics']['words_total']}",
            f"Speed: {metrics['speech_metrics']['words_per_minute']:.1f} WPM",
            f"Language: {metrics['speech_metrics']['language']}",
            "",
            "VOICE ACTIVITY",
            "-" * 30,
            f"Speech ratio: {metrics['vad_analysis']['speech_ratio']:.1%}",
            f"Pauses: {metrics['vad_analysis']['pause_count']}",
            f"Avg pause: {metrics['vad_analysis']['avg_pause_duration']:.1f}s",
            "",
            "PROSODY",
            "-" * 30,
            f"Pitch mean: {metrics['prosody_metrics']['pitch_mean_hz']:.1f} Hz",
            f"Pitch range: {metrics['prosody_metrics']['pitch_range_hz']:.1f} Hz",
            f"Energy variation: {metrics['prosody_metrics']['energy_cv']:.2f}",
            "",
            "EMOTION",
            "-" * 30,
            f"Dominant: {metrics['emotion_metrics']['dominant_emotion']}",
            f"Confidence: {metrics['emotion_metrics']['confidence']:.1%}",
            "",
            "FILLER WORDS",
            "-" * 30,
            f"Count: {metrics['filler_metrics']['filler_word_count']}",
            f"Ratio: {metrics['filler_metrics']['fillers_per_100_words']:.1f} per 100 words",
            "",
            "=" * 60
        ]
        
        return "\n".join(lines)
    
    def _create_multi_speaker_report(self, metrics: Dict[str, Any]) -> str:
        """Create multi-speaker report."""
        lines = [
            "=" * 60,
            "Multi-Speaker Conversation Analysis Report",
            "=" * 60,
            "",
            f"File: {metrics['audio_info']['file_name']}",
            f"Duration: {metrics['audio_info']['duration_seconds']:.1f}s",
            "",
            "CONVERSATION OVERVIEW",
            "-" * 30,
            f"Number of speakers: {metrics['conversation_metrics'].get('num_speakers', 'N/A')}",
            f"Total turns: {metrics['conversation_metrics'].get('total_turns', 'N/A')}",
            f"Speaker changes: {metrics['conversation_metrics'].get('speaker_changes', 'N/A')}",
            "",
            "SPEAKER PROFILES",
            "-" * 30
        ]
        
        for profile in metrics.get('speaker_profiles', []):
            lines.append(f"\n{profile.get('speaker_label', 'Unknown')}:")
            lines.append(f"  Speaking time: {profile.get('total_speaking_time', 0):.1f}s")
            lines.append(f"  Turn count: {profile.get('turn_count', 0)}")
            lines.append(f"  Avg turn duration: {profile.get('avg_turn_duration', 0):.1f}s")
            if 'acoustic_profile' in profile:
                ap = profile['acoustic_profile']
                lines.append(f"  Avg pitch: {ap.get('avg_pitch_hz', 0):.1f} Hz")
        
        lines.extend([
            "",
            "CONVERSATIONAL FLOW",
            "-" * 30,
            f"Fluency score: {metrics['conversation_metrics'].get('fluency_score', 0):.3f}",
            f"Engagement score: {metrics['conversation_metrics'].get('engagement_score', 0):.3f}",
            f"Balance score: {metrics['conversation_metrics'].get('balance_score', 0):.3f}",
            "",
            "=" * 60
        ])
        
        return "\n".join(lines)
    
    def _create_summary_report(self, metrics: Dict[str, Any]) -> str:
        """Create summary report."""
        if "conversation_timeline" in metrics:
            # Multi-speaker
            conv_metrics = metrics.get('conversation_metrics', {})
            return (
                f"Duration: {metrics['audio_info']['duration_seconds']:.1f}s | "
                f"Speakers: {conv_metrics.get('num_speakers', 'N/A')} | "
                f"Fluency: {conv_metrics.get('fluency_score', 0):.2f} | "
                f"Engagement: {conv_metrics.get('engagement_score', 0):.2f}"
            )
        else:
            # Single-speaker
            return (
                f"Duration: {metrics['audio_info']['duration_seconds']:.1f}s | "
                f"Speed: {metrics['speech_metrics']['words_per_minute']:.1f} WPM | "
                f"Speech: {metrics['vad_analysis']['speech_ratio']:.1%} | "
                f"Fillers: {metrics['filler_metrics']['fillers_per_100_words']:.1f}/100w"
            )
    
    def _create_detailed_report(self, metrics: Dict[str, Any]) -> str:
        """Create detailed report with all metrics."""
        if "conversation_timeline" in metrics:
            return self._create_detailed_multi_speaker_report(metrics)
        else:
            return self._create_detailed_single_speaker_report(metrics)
    
    def _create_detailed_single_speaker_report(self, metrics: Dict[str, Any]) -> str:
        """Create detailed single-speaker report."""
        lines = [
            "# Sales Audio Analysis Report",
            "",
            "## Audio Information",
            f"- File: {metrics['audio_info']['file_name']}",
            f"- Duration: {metrics['audio_info']['duration_seconds']:.2f}s",
            f"- Sample Rate: {metrics['audio_info']['sample_rate']} Hz",
            f"- File Size: {metrics['audio_info']['file_size_mb']:.2f} MB",
            "",
            "## Speech Metrics",
            f"- Total Words: {metrics['speech_metrics']['words_total']}",
            f"- Speaking Rate: {metrics['speech_metrics']['words_per_minute']:.1f} WPM",
            f"- Language: {metrics['speech_metrics']['language']}",
            "",
            "## Voice Activity Detection",
            f"- Speech Duration: {metrics['vad_analysis']['speech_duration']:.2f}s",
            f"- Silence Duration: {metrics['vad_analysis']['silence_duration']:.2f}s",
            f"- Speech Ratio: {metrics['vad_analysis']['speech_ratio']:.1%}",
            f"- Total Pauses: {metrics['vad_analysis']['pause_count']}",
            f"- Average Pause: {metrics['vad_analysis']['avg_pause_duration']:.2f}s",
            f"- Long Pauses (>2s): {metrics['vad_analysis']['long_pause_count']}",
            "",
            "## Prosody Analysis",
            f"- Pitch Mean: {metrics['prosody_metrics']['pitch_mean_hz']:.1f} Hz",
            f"- Pitch Std Dev: {metrics['prosody_metrics']['pitch_std_hz']:.1f} Hz",
            f"- Pitch Range: {metrics['prosody_metrics']['pitch_range_hz']:.1f} Hz",
            f"- Energy Mean: {metrics['prosody_metrics']['energy_mean']:.4f}",
            f"- Energy Variation: {metrics['prosody_metrics']['energy_cv']:.3f}",
            "",
            "## Emotion Analysis",
            f"- Dominant Emotion: {metrics['emotion_metrics']['dominant_emotion']}",
            f"- Confidence: {metrics['emotion_metrics']['confidence']:.1%}",
            "",
            "## Filler Words",
            f"- Total Count: {metrics['filler_metrics']['filler_word_count']}",
            f"- Ratio: {metrics['filler_metrics']['fillers_per_100_words']:.1f} per 100 words",
            "",
            "## Transcript",
            "```",
            metrics['transcript']['text'],
            "```"
        ]
        
        return "\n".join(lines)
    
    def _create_detailed_multi_speaker_report(self, metrics: Dict[str, Any]) -> str:
        """Create detailed multi-speaker report."""
        lines = [
            "# Multi-Speaker Conversation Analysis Report",
            "",
            "## Audio Information",
            f"- File: {metrics['audio_info']['file_name']}",
            f"- Duration: {metrics['audio_info']['duration_seconds']:.2f}s",
            f"- Sample Rate: {metrics['audio_info']['sample_rate']} Hz",
            "",
            "## Conversation Metrics",
            f"- Number of Speakers: {metrics['conversation_metrics'].get('num_speakers', 'N/A')}",
            f"- Total Turns: {metrics['conversation_metrics'].get('total_turns', 'N/A')}",
            f"- Speaker Changes: {metrics['conversation_metrics'].get('speaker_changes', 'N/A')}",
            f"- Overlap Ratio: {metrics['conversation_metrics'].get('overlap_ratio', 0):.1%}",
            f"- Mean Response Latency: {metrics['conversation_metrics'].get('mean_response_latency', 0):.2f}s",
            "",
            "## Speaker Profiles"
        ]
        
        for profile in metrics.get('speaker_profiles', []):
            lines.append(f"\n### {profile.get('speaker_label', 'Unknown')} ({profile.get('speaker_id', 'N/A')})")
            lines.append(f"- Speaking Time: {profile.get('total_speaking_time', 0):.2f}s")
            lines.append(f"- Turn Count: {profile.get('turn_count', 0)}")
            lines.append(f"- Avg Turn Duration: {profile.get('avg_turn_duration', 0):.2f}s")
            lines.append(f"- Overlap Ratio: {profile.get('overlap_ratio', 0):.1%}")
            
            if 'acoustic_profile' in profile:
                ap = profile['acoustic_profile']
                lines.append(f"- Avg Pitch: {ap.get('avg_pitch_hz', 0):.1f} Hz")
                lines.append(f"- Pitch Std Dev: {ap.get('pitch_std_hz', 0):.1f} Hz")
                lines.append(f"- Avg Energy: {ap.get('avg_energy', 0):.6f}")
        
        lines.extend([
            "",
            "## Global Acoustic Metrics",
            f"- Avg Pitch: {metrics['global_acoustic_metrics'].get('pitch_mean_hz', 0):.1f} Hz",
            f"- Pitch Std Dev: {metrics['global_acoustic_metrics'].get('pitch_std_hz', 0):.1f} Hz",
            f"- Energy CV: {metrics['global_acoustic_metrics'].get('energy_cv', 0):.3f}",
            "",
            "## Processing Metadata",
            f"- Analyzer Version: {metrics['processing_meta'].get('version', 'unknown')}",
            f"- Processing Time: {metrics['processing_meta'].get('processing_time_seconds', 0):.2f}s",
            f"- Timestamp: {metrics['processing_meta'].get('timestamp', 'unknown')}"
        ])
        
        return "\n".join(lines)
