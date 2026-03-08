"""
JSON Exporter Module
Exports analysis results to JSON and generates LLM prompts
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class JSONExporter:
    """Export analysis results to JSON"""
    
    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """
        Initialize JSON exporter
        
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
        Export metrics to JSON file
        
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
    
    def export_compact(
        self,
        metrics: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Export compact JSON (no whitespace)
        
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
    
    def generate_llm_prompt(
        self,
        metrics: Dict[str, Any],
        prompt_template: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate LLM prompt with analysis data
        
        Args:
            metrics: Analysis metrics
            prompt_template: Prompt template text
            output_path: Optional output file path
            
        Returns:
            Generated prompt text
        """
        # Prepare analysis JSON for prompt
        analysis_data = {
            "audio_info": metrics["audio_info"],
            "vad_analysis": metrics["vad_analysis"],
            "speech_metrics": metrics["speech_metrics"],
            "prosody_metrics": metrics["prosody_metrics"],
            "emotion_metrics": metrics["emotion_metrics"],
            "filler_metrics": metrics["filler_metrics"],
            "transcript_summary": {
                "word_count": metrics["speech_metrics"]["words_total"],
                "language": metrics["transcript"]["language"],
                "first_500_chars": metrics["transcript"]["text"][:500] + "..."
            }
        }
        
        # Replace placeholder in template
        analysis_json = json.dumps(
            analysis_data,
            indent=2,
            ensure_ascii=self.ensure_ascii
        )
        
        prompt = prompt_template.replace("{{analysis_json}}", analysis_json)
        
        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
        
        return prompt
    
    def export_with_prompt(
        self,
        metrics: Dict[str, Any],
        prompt_template: str,
        json_output: str,
        prompt_output: str
    ) -> Dict[str, str]:
        """
        Export both JSON and LLM prompt
        
        Args:
            metrics: Analysis metrics
            prompt_template: Prompt template
            json_output: JSON output path
            prompt_output: Prompt output path
            
        Returns:
            Dictionary with output paths
        """
        # Export JSON
        json_path = self.export(metrics, json_output)
        
        # Generate and export prompt
        prompt_path = self.generate_llm_prompt(
            metrics,
            prompt_template,
            prompt_output
        )
        
        return {
            "json_path": json_path,
            "prompt_path": prompt_path
        }
    
    def create_report(
        self,
        metrics: Dict[str, Any],
        template: str = "default"
    ) -> str:
        """
        Create human-readable report
        
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
        """Create default report"""
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
    
    def _create_summary_report(self, metrics: Dict[str, Any]) -> str:
        """Create summary report"""
        return (
            f"Duration: {metrics['audio_info']['duration_seconds']:.1f}s | "
            f"Speed: {metrics['speech_metrics']['words_per_minute']:.1f} WPM | "
            f"Speech: {metrics['vad_analysis']['speech_ratio']:.1%} | "
            f"Fillers: {metrics['filler_metrics']['fillers_per_100_words']:.1f}/100w"
        )
    
    def _create_detailed_report(self, metrics: Dict[str, Any]) -> str:
        """Create detailed report with all metrics"""
        # Include full transcript and all details
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
