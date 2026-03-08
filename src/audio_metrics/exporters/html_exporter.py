"""
HTML Exporter Module
====================
Export metrics to interactive HTML format.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from jinja2 import Template

from core.logger import get_logger

logger = get_logger(__name__)


# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Metrics Report - {{ file_name }}</title>
    <style>
        :root {
            --primary: #2563eb;
            --secondary: #64748b;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }

        .container { max-width: 1200px; margin: 0 auto; }

        header {
            text-align: center;
            margin-bottom: 2rem;
        }

        h1 { color: var(--primary); margin-bottom: 0.5rem; }
        .subtitle { color: var(--secondary); }

        .card {
            background: var(--card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .card h2 {
            color: var(--primary);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--bg);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }

        .metric {
            background: var(--bg);
            padding: 1rem;
            border-radius: 8px;
        }

        .metric-label {
            color: var(--secondary);
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }

        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text);
        }

        .metric-unit {
            font-size: 0.875rem;
            color: var(--secondary);
            font-weight: normal;
        }

        .progress-bar {
            height: 8px;
            background: var(--bg);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }

        .progress-fill {
            height: 100%;
            background: var(--primary);
            transition: width 0.3s ease;
        }

        .tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .tag-success { background: #dcfce7; color: #166534; }
        .tag-warning { background: #fef3c7; color: #92400e; }
        .tag-info { background: #dbeafe; color: #1e40af; }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--bg);
        }

        th {
            font-weight: 600;
            color: var(--secondary);
            font-size: 0.875rem;
        }

        .emotion-bar {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .emotion-label { width: 80px; font-size: 0.875rem; }
        .emotion-track { flex: 1; height: 8px; background: var(--bg); border-radius: 4px; }
        .emotion-fill { height: 100%; border-radius: 4px; }
        .emotion-value { width: 50px; text-align: right; font-size: 0.875rem; }

        .footer {
            text-align: center;
            color: var(--secondary);
            font-size: 0.875rem;
            margin-top: 2rem;
        }

        @media print {
            body { padding: 1rem; }
            .card { box-shadow: none; border: 1px solid #e2e8f0; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Audio Metrics Report</h1>
            <p class="subtitle">{{ file_name }}</p>
        </header>

        <!-- Audio Info -->
        <div class="card">
            <h2>Audio Information</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Duration</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.audio_info.duration_seconds) }}<span class="metric-unit">s</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Sample Rate</div>
                    <div class="metric-value">{{ metrics.audio_info.sample_rate }}<span class="metric-unit">Hz</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label">File Size</div>
                    <div class="metric-value">{{ "%.2f"|format(metrics.audio_info.file_size_mb) }}<span class="metric-unit">MB</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Language</div>
                    <div class="metric-value">{{ metrics.speech_metrics.language|upper }}</div>
                </div>
            </div>
        </div>

        <!-- VAD Analysis -->
        <div class="card">
            <h2>Voice Activity Analysis</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Speech Ratio</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.vad_analysis.speech_ratio * 100) }}<span class="metric-unit">%</span></div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ metrics.vad_analysis.speech_ratio * 100 }}%"></div>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Speech Duration</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.vad_analysis.speech_duration) }}<span class="metric-unit">s</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Pause Count</div>
                    <div class="metric-value">{{ metrics.vad_analysis.pause_count }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Avg Pause</div>
                    <div class="metric-value">{{ "%.2f"|format(metrics.vad_analysis.avg_pause_duration) }}<span class="metric-unit">s</span></div>
                </div>
            </div>
        </div>

        <!-- Speech Metrics -->
        <div class="card">
            <h2>Speech Metrics</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Total Words</div>
                    <div class="metric-value">{{ metrics.speech_metrics.words_total }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Speaking Rate</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.speech_metrics.words_per_minute) }}<span class="metric-unit">WPM</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Filler Words</div>
                    <div class="metric-value">{{ metrics.filler_metrics.filler_word_count }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Fillers per 100 words</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.filler_metrics.fillers_per_100_words) }}</div>
                </div>
            </div>
        </div>

        <!-- Prosody -->
        <div class="card">
            <h2>Prosody Analysis</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Pitch Mean</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.prosody_metrics.pitch_mean_hz) }}<span class="metric-unit">Hz</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Pitch Std</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.prosody_metrics.pitch_std_hz) }}<span class="metric-unit">Hz</span></div>
                </div>
                <div class="metric">
                    <div class="metric-label">Energy Mean</div>
                    <div class="metric-value">{{ "%.4f"|format(metrics.prosody_metrics.energy_mean) }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Energy CV</div>
                    <div class="metric-value">{{ "%.3f"|format(metrics.prosody_metrics.energy_cv) }}</div>
                </div>
            </div>
        </div>

        <!-- Emotion -->
        <div class="card">
            <h2>Emotion Analysis</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Dominant Emotion</div>
                    <div class="metric-value">
                        <span class="tag tag-{% if metrics.emotion_metrics.confidence > 0.7 %}success{% elif metrics.emotion_metrics.confidence > 0.4 %}warning{% else %}info{% endif %}">
                            {{ metrics.emotion_metrics.dominant_emotion|upper }}
                        </span>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Confidence</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.emotion_metrics.confidence * 100) }}<span class="metric-unit">%</span></div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ metrics.emotion_metrics.confidence * 100 }}%"></div>
                    </div>
                </div>
            </div>

            {% if metrics.emotion_metrics.emotion_probabilities %}
            <h3 style="margin-top: 1rem; margin-bottom: 0.5rem;">Emotion Distribution</h3>
            {% for emotion, prob in metrics.emotion_metrics.emotion_probabilities.items() %}
            <div class="emotion-bar">
                <div class="emotion-label">{{ emotion }}</div>
                <div class="emotion-track">
                    <div class="emotion-fill" style="width: {{ prob * 100 }}%; background: {{ loop.cycle('#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4') }}"></div>
                </div>
                <div class="emotion-value">{{ "%.1f"|format(prob * 100) }}%</div>
            </div>
            {% endfor %}
            {% endif %}
        </div>

        <!-- Transcript -->
        {% if metrics.transcript.text %}
        <div class="card">
            <h2>Transcript</h2>
            <p style="white-space: pre-wrap; color: var(--secondary);">{{ metrics.transcript.text }}</p>
        </div>
        {% endif %}

        <div class="footer">
            Generated by Audio Metrics CLI | {{ timestamp }}
        </div>
    </div>
</body>
</html>
"""


class HTMLExporter:
    """Export metrics to interactive HTML format."""

    def export(self, metrics: Dict[str, Any], output_path: str) -> str:
        """
        Export metrics to HTML file.

        Args:
            metrics: Analysis metrics dictionary
            output_path: Output file path

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare template data
        template_data = {
            "metrics": metrics,
            "file_name": metrics.get("audio_info", {}).get("file_name", "Unknown"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Render template
        template = Template(HTML_TEMPLATE)
        html_content = template.render(**template_data)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("HTML exported", path=str(output_path))
        return str(output_path)


class BatchHTMLExporter:
    """Export batch results to HTML."""

    def export_batch(self, results: List[Dict[str, Any]], output_path: str) -> str:
        """
        Export batch results to HTML.

        Args:
            results: List of analysis results
            output_path: Output file path

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        template_data = {
            "results": results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": len(results)
        }

        # Create a simpler template for batch results
        batch_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Metrics Report - Batch Analysis</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 2rem; background: #f8fafc; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #2563eb; margin-bottom: 1rem; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background: #f1f5f9; font-weight: 600; color: #475569; }
        tr:hover { background: #f8fafc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Audio Metrics Report - Batch Analysis</h1>
        <p>Total files: {{ total_files }}</p>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Duration (s)</th>
                    <th>WPM</th>
                    <th>Speech Ratio</th>
                    <th>Fillers/100w</th>
                    <th>Pitch (Hz)</th>
                    <th>Emotion</th>
                </tr>
            </thead>
            <tbody>
            {% for result in results %}
                <tr>
                    <td>{{ result.audio_info.file_name }}</td>
                    <td>{{ "%.1f"|format(result.audio_info.duration_seconds) }}</td>
                    <td>{{ "%.1f"|format(result.speech_metrics.words_per_minute) }}</td>
                    <td>{{ "%.1f"|format(result.vad_analysis.speech_ratio * 100) }}%</td>
                    <td>{{ "%.1f"|format(result.filler_metrics.fillers_per_100_words) }}</td>
                    <td>{{ "%.1f"|format(result.prosody_metrics.pitch_mean_hz) }}</td>
                    <td>{{ result.emotion_metrics.dominant_emotion }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
        """

        template = Template(batch_template)
        html_content = template.render(**template_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Batch HTML exported", path=str(output_path), files=len(results))
        return str(output_path)
