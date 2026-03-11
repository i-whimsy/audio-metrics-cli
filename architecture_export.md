# Audio Metrics CLI - 架构信息导出

**导出时间**: 2026-03-11 07:59  
**用途**: 外部架构评估

---

## 1. 项目基本信息

| 项目 | 信息 |
|------|------|
| **项目名称** | Audio Metrics CLI |
| **当前版本** | v2.0.0 (Enhanced) |
| **Python 版本** | 3.8+ |
| **主要依赖库** | whisper, librosa, torch, pyannote.audio, click, tqdm |

---

## 2. 项目目录结构

```
audio-metrics-cli/
├── src/
│   └── audio_metrics/
│       ├── __init__.py
│       ├── cli.py                    # CLI 入口
│       ├── cli_enhanced.py           # 增强版 CLI (v2.0)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py             # 配置管理
│       │   ├── logger.py             # 日志系统
│       │   └── model_config.py       # 模型离线配置 (新增)
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── audio_loader.py       # 音频加载
│       │   ├── vad_analyzer.py       # 语音活动检测
│       │   ├── speech_to_text.py     # Whisper 转录
│       │   ├── prosody_analyzer.py   # 韵律分析
│       │   ├── emotion_analyzer.py   # 情感识别
│       │   ├── filler_detector.py    # 填充词检测
│       │   ├── speaker_diarization.py # 说话人分离
│       │   ├── timeline_builder.py   # 时间线构建
│       │   ├── segment_metrics.py    # 片段指标
│       │   ├── speaker_metrics.py    # 说话人指标
│       │   ├── timing_relation.py    # 时序关系
│       │   ├── metrics_builder.py    # 指标构建器
│       │   ├── summary_generator.py  # 摘要生成 (新增)
│       │   └── keyword_extractor.py  # 关键词提取 (新增)
│       └── exporters/
│           ├── __init__.py
│           ├── json_exporter.py      # JSON 导出
│           └── enhanced_json_exporter.py # 增强 JSON 导出 (新增)
├── outputs/
│   └── test_results/
├── docs/
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 3. CLI 入口代码

**文件**: `src/audio_metrics/cli_enhanced.py` (v2.0 增强版)

```python
#!/usr/bin/env python3
"""
Audio Metrics CLI - Enhanced Version v2.0
Unified analysis with automatic speaker detection, summary generation, and rich JSON output
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import click
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "audio_metrics"))

from core.logger import setup_logging, get_logger
from core.config import Config
from modules.audio_loader import AudioLoader
from modules.vad_analyzer import VADAnalyzer
from modules.speech_to_text import SpeechToText
from modules.prosody_analyzer import ProsodyAnalyzer
from modules.emotion_analyzer import EmotionAnalyzer
from modules.filler_detector import FillerDetector
from modules.speaker_diarization import SpeakerDiarization
from modules.timeline_builder import TimelineBuilder
from modules.segment_metrics import SegmentMetricsExtractor
from modules.speaker_metrics import SpeakerMetricsAggregator
from modules.timing_relation import TimingRelationAnalyzer
from modules.summary_generator import SummaryGenerator
from modules.keyword_extractor import KeywordExtractor
from exporters.enhanced_json_exporter import EnhancedJSONExporter

logger = get_logger(__name__)


@click.group()
@click.version_option(version="2.0.0")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--log-file", type=click.Path(), default=None, help="Log file path")
@click.pass_context
def main(ctx, verbose, log_file):
    """Audio Metrics CLI v2.0 - Enhanced audio analysis with automatic speaker detection"""
    level = "DEBUG" if verbose else "INFO"
    setup_logging(level=level, log_file=log_file, json_output=False)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = Config()


@main.command("analyze")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_file", type=click.Path(), default=None, help="Output JSON file")
@click.option("-m", "--model", "stt_model", default="base", help="Whisper model")
@click.option("--no-emotion", is_flag=True, help="Skip emotion analysis")
@click.option("--diarization", type=click.Choice(["auto", "on", "off"]), default="auto", help="Speaker diarization mode")
@click.option("--min-speakers", type=int, default=1, help="Minimum speakers (hint)")
@click.option("--max-speakers", type=int, default=10, help="Maximum speakers (hint)")
@click.option("--summary", type=click.Choice(["auto", "llm", "cloud", "heuristic", "none"]), default="auto", help="Summary generation method")
@click.option("--show-progress", is_flag=True, help="Show progress steps")
@click.pass_context
def analyze(ctx, audio_file, output_file, stt_model, no_emotion, diarization, min_speakers, max_speakers, summary, show_progress):
    """
    Analyze audio file with automatic speaker detection and rich JSON output.
    
    AUDIO_FILE: Path to audio file (wav, mp3, m4a, flac, etc.)
    """
    verbose = ctx.obj.get("verbose", False)
    config = ctx.obj.get("config", Config())
    
    if stt_model:
        config.models.speech_to_text.model = stt_model
    if no_emotion:
        config.features.enable_emotion = False
    
    click.echo("=" * 60)
    click.echo("Audio Metrics CLI v2.0 - Enhanced Analysis")
    click.echo("=" * 60)
    click.echo(f"Input: {Path(audio_file).name}")
    click.echo(f"Diarization: {diarization}")
    click.echo(f"Summary: {summary}")
    click.echo("")
    
    start_time = time.time()
    
    try:
        # STEP 1: Load audio
        if show_progress:
            click.echo("[1/9] Loading audio...")
        loader = AudioLoader(audio_file)
        loader.load()
        audio_info = loader.get_audio_info()
        audio_data = loader.get_audio_data()
        if show_progress:
            click.echo(f"  [OK] Duration: {audio_info['duration_seconds']:.2f}s")
        
        # STEP 2: VAD analysis
        if show_progress:
            click.echo("[2/9] Voice activity detection...")
        vad = VADAnalyzer()
        vad_analysis = vad.analyze(audio_data)
        if show_progress:
            click.echo(f"  [OK] Speech ratio: {vad_analysis['speech_ratio']:.1%}")
        
        # STEP 3: Speech-to-text
        if show_progress:
            click.echo("[3/9] Speech-to-text...")
        stt = SpeechToText(model_name=config.models.speech_to_text.model)
        transcript = stt.transcribe(audio_file)
        if show_progress:
            click.echo(f"  [OK] Language: {transcript.get('language', 'unknown')}")
        
        # STEP 4: Prosody analysis
        if show_progress:
            click.echo("[4/9] Prosody analysis...")
        prosody = ProsodyAnalyzer(sample_rate=audio_info['sample_rate'])
        prosody_metrics = prosody.analyze(audio_data)
        
        # STEP 5: Emotion analysis
        emotion_metrics = {"dominant_emotion": "neutral", "confidence": 0.5}
        if config.features.enable_emotion:
            try:
                emotion = EmotionAnalyzer()
                emotion_metrics = emotion.analyze(audio_file)
            except Exception as e:
                logger.warning(f"Emotion analysis failed: {e}")
        
        # STEP 6: Filler detection
        if show_progress:
            click.echo("[6/9] Filler word detection...")
        filler = FillerDetector(language=transcript.get('language', 'en'))
        filler_metrics = filler.detect(transcript.get('text', ''))
        
        # STEP 7: Speaker diarization (auto/on/off)
        diarization_result = None
        segments = []
        
        if diarization != "off":
            if show_progress:
                click.echo("[7/9] Speaker diarization...")
            try:
                diarizer = SpeakerDiarization()
                diarization_result = diarizer.diarize(
                    audio_file,
                    min_speakers=min_speakers if diarization == "on" else None,
                    max_speakers=max_speakers if diarization == "on" else None
                )
                
                timeline_builder = TimelineBuilder()
                conversation_timeline = timeline_builder.build(
                    diarization_segments=diarization_result.get('segments', []),
                    audio_duration=audio_info['duration_seconds']
                )
                
                segment_extractor = SegmentMetricsExtractor(sample_rate=audio_info['sample_rate'])
                segment_metrics_list = segment_extractor.extract(audio_data, diarization_result.get('segments', []))
                
                segments = _build_enriched_segments(
                    diarization_result.get('segments', []),
                    transcript.get('text', ''),
                    segment_metrics_list
                )
                
                if show_progress:
                    click.echo(f"  [OK] Detected {diarization_result['num_speakers']} speakers")
                    
            except Exception as e:
                logger.warning(f"Diarization failed: {e}")
        
        # STEP 8: Generate summary and keywords
        if show_progress:
            click.echo("[8/9] Generating summary and keywords...")
        
        summary_gen = SummaryGenerator(method=summary)
        summary_result = summary_gen.generate(transcript.get('text', ''), {
            "duration": audio_info['duration_seconds'],
            "speech_ratio": vad_analysis.get('speech_ratio', 0)
        })
        
        keyword_ext = KeywordExtractor(language=transcript.get('language', 'zh'))
        keywords_result = keyword_ext.extract(transcript.get('text', ''), segments)
        
        if show_progress:
            click.echo(f"  [OK] Summary: {summary_result.get('method', 'none')}")
            click.echo(f"  [OK] Topics: {len(keywords_result.get('topics', []))}")
        
        # STEP 9: Export enhanced JSON
        if show_progress:
            click.echo("[9/9] Exporting JSON...")
        
        if output_file is None:
            audio_path = Path(audio_file)
            output_dir = Path("outputs") / audio_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "analysis_result.json"
        
        exporter = EnhancedJSONExporter()
        output_path = exporter.export(
            audio_info=audio_info,
            vad_analysis=vad_analysis,
            transcript_result=transcript,
            prosody_metrics=prosody_metrics,
            emotion_metrics=emotion_metrics,
            filler_metrics=filler_metrics,
            diarization_result=diarization_result,
            segments=segments,
            summary=summary_result,
            keywords=keywords_result,
            output_path=str(output_file)
        )
        
        processing_time = time.time() - start_time
        click.echo("")
        click.echo("=" * 60)
        click.echo("Analysis Complete")
        click.echo("=" * 60)
        click.echo(f"Duration: {audio_info['duration_seconds']:.1f}s")
        click.echo(f"Speech ratio: {vad_analysis['speech_ratio']:.1%}")
        click.echo(f"Speakers: {diarization_result['num_speakers'] if diarization_result else 'N/A'}")
        click.echo(f"Words: {len(transcript.get('text', ''))} chars")
        click.echo(f"Summary: {summary_result.get('one_liner', 'N/A')[:50]}...")
        click.echo(f"Processing time: {processing_time:.2f}s")
        click.echo("")
        click.echo(f"[OK] Exported: {output_path}")
        click.echo("")
        
    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _build_enriched_segments(diarization_segments, full_transcript, segment_metrics):
    """Build enriched segments with text, speaker, and acoustic features"""
    enriched = []
    transcript_chars = list(full_transcript)
    char_index = 0
    
    for i, seg in enumerate(diarization_segments[:50]):
        seg_duration = seg.get('duration', 1.0)
        estimated_chars = max(10, int(seg_duration * 5))
        
        start_idx = char_index
        end_idx = min(char_index + estimated_chars, len(transcript_chars))
        seg_text = ''.join(transcript_chars[start_idx:end_idx])
        char_index = end_idx
        
        acoustic = segment_metrics[i] if i < len(segment_metrics) else {}
        
        enriched.append({
            "start": round(seg.get('start', 0), 2),
            "end": round(seg.get('end', 0), 2),
            "speaker": seg.get('speaker', 'SPEAKER_00'),
            "text": seg_text,
            "emotion": "neutral",
            "pitch": acoustic.get('pitch_mean_hz', 0),
            "energy": acoustic.get('energy_mean', 0)
        })
    
    return enriched


if __name__ == "__main__":
    main()
```

---

## 4. Pipeline 主流程

**文件**: `src/audio_metrics/cli_enhanced.py` (内嵌在 analyze 命令中)

**9 步处理流程**:

```
[1] 加载音频 → AudioLoader.load()
    ↓
[2] VAD 语音检测 → VADAnalyzer.analyze()
    ↓
[3] 语音转录 → SpeechToText.transcribe()
    ↓
[4] 韵律分析 → ProsodyAnalyzer.analyze()
    ↓
[5] 情感识别 → EmotionAnalyzer.analyze() (可选)
    ↓
[6] 填充词检测 → FillerDetector.detect()
    ↓
[7] 说话人分离 → SpeakerDiarization.diarize()
    ↓
[8] 摘要&关键词 → SummaryGenerator + KeywordExtractor
    ↓
[9] JSON 导出 → EnhancedJSONExporter.export()
```

---

## 5. Speaker Diarization 模块

**文件**: `src/audio_metrics/modules/speaker_diarization.py`

```python
"""
Speaker Diarization Module
==========================
Identifies and separates different speakers in audio.

Uses pyannote.audio when available, falls back to simple VAD-based segmentation.
"""

import os
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)


class SpeakerDiarization:
    """Speaker diarization - identifies 'who spoke when'"""
    
    def __init__(self, model_name: str = "pyannote/speaker-diarization-3.1"):
        self.model_name = model_name
        self.model = None
        self.segments = []
        self.use_fallback = False
        
    def load_model(self):
        """Load speaker diarization model with offline-first strategy"""
        if self.model is not None:
            return
        
        import torch
        
        # Set offline environment variables
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['TORCH_HOME'] = str(Path.home() / ".cache" / "torch")
            
        try:
            from pyannote.audio import Pipeline
            
            self.model = Pipeline.from_pretrained(self.model_name)
            
            if torch.cuda.is_available():
                self.model.to(torch.device("cuda"))
                logger.info("Speaker diarization model loaded on GPU")
            else:
                logger.info("Speaker diarization model loaded on CPU")
                
            self.use_fallback = False
                
        except Exception as e:
            logger.warning("pyannote.audio not available, using fallback", error=str(e))
            self.use_fallback = True
            self.model = None
    
    def diarize(self, audio_path: str, num_speakers: Optional[int] = None,
                min_speakers: Optional[int] = None, max_speakers: Optional[int] = None) -> Dict[str, Any]:
        """Perform speaker diarization on audio file"""
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if self.model is None:
            self.load_model()
        
        if self.use_fallback:
            return self._fallback_diarize(str(audio_path))
        
        # Run pyannote pipeline
        diarization = self.model(str(audio_path))
        
        # Extract segments
        segments = []
        speakers = set()
        
        for segment, track, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'start': segment.start,
                'end': segment.end,
                'speaker': speaker,
                'duration': segment.end - segment.start
            })
            speakers.add(speaker)
        
        return {
            'num_speakers': len(speakers),
            'speakers': list(speakers),
            'segments': sorted(segments, key=lambda x: x['start'])
        }
    
    def _fallback_diarize(self, audio_path: str) -> Dict[str, Any]:
        """Fallback VAD-based segmentation"""
        from modules.vad_analyzer import VADAnalyzer
        
        vad = VADAnalyzer()
        vad_result = vad.analyze(audio_path)
        
        segments = []
        for i, seg in enumerate(vad_result.get('speech_segments', [])):
            segments.append({
                'start': seg['start'],
                'end': seg['end'],
                'speaker': f'SPEAKER_{i % 2:02d}',
                'duration': seg['duration']
            })
        
        return {
            'num_speakers': 2,
            'speakers': ['SPEAKER_00', 'SPEAKER_01'],
            'segments': segments
        }
```

---

## 6. Conversation Timeline 构建

**文件**: `src/audio_metrics/modules/timeline_builder.py`

```python
"""
Timeline Builder Module
Builds chronological conversation timeline from diarization segments
"""

from typing import Dict, Any, List


class TimelineBuilder:
    """Build conversation timeline from speaker segments"""
    
    def build(self, diarization_segments: List[Dict], audio_duration: float) -> List[Dict]:
        """
        Build conversation timeline
        
        Args:
            diarization_segments: Segments from speaker diarization
            audio_duration: Total audio duration
            
        Returns:
            Timeline with conversation events
        """
        timeline = []
        
        # Sort segments by start time
        sorted_segments = sorted(diarization_segments, key=lambda x: x['start'])
        
        prev_end = 0
        for seg in sorted_segments:
            # Add silence gap if exists
            if seg['start'] > prev_end:
                timeline.append({
                    'type': 'silence',
                    'start': prev_end,
                    'end': seg['start'],
                    'duration': seg['start'] - prev_end
                })
            
            # Add speech segment
            timeline.append({
                'type': 'speech',
                'start': seg['start'],
                'end': seg['end'],
                'duration': seg['duration'],
                'speaker': seg.get('speaker', 'UNKNOWN')
            })
            
            prev_end = seg['end']
        
        # Add final silence if exists
        if prev_end < audio_duration:
            timeline.append({
                'type': 'silence',
                'start': prev_end,
                'end': audio_duration,
                'duration': audio_duration - prev_end
            })
        
        return timeline
    
    def get_statistics(self, timeline: List[Dict]) -> Dict[str, Any]:
        """Extract timeline statistics"""
        speech_segments = [s for s in timeline if s['type'] == 'speech']
        silence_segments = [s for s in timeline if s['type'] == 'silence']
        
        return {
            'speech_segments': len(speech_segments),
            'silence_segments': len(silence_segments),
            'total_speech_duration': sum(s['duration'] for s in speech_segments),
            'total_silence_duration': sum(s['duration'] for s in silence_segments)
        }
```

---

## 7. Metrics 提取模块

### 7.1 Prosody Analyzer (韵律分析)

**文件**: `src/audio_metrics/modules/prosody_analyzer.py`

```python
"""
Prosody Analyzer Module
Extracts pitch, energy, and other prosodic features
"""

import numpy as np
from typing import Dict, Any
import librosa


class ProsodyAnalyzer:
    """Analyze prosodic features of speech"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
    def analyze(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Analyze prosodic features"""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        pitch_features = self._extract_pitch(audio_data)
        energy_features = self._extract_energy(audio_data)
        
        return {**pitch_features, **energy_features}
    
    def _extract_pitch(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Extract pitch (F0) features using YIN algorithm"""
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio_data,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7'),
                sr=self.sample_rate
            )
            
            voiced_f0 = f0[voiced_flag]
            
            if len(voiced_f0) > 0:
                return {
                    'pitch_mean_hz': float(np.mean(voiced_f0)),
                    'pitch_std_hz': float(np.std(voiced_f0)),
                    'pitch_min_hz': float(np.min(voiced_f0)),
                    'pitch_max_hz': float(np.max(voiced_f0)),
                    'pitch_range_hz': float(np.max(voiced_f0) - np.min(voiced_f0)),
                    'voiced_ratio': float(np.mean(voiced_flag))
                }
        except Exception as e:
            pass
        
        return {
            'pitch_mean_hz': 0,
            'pitch_std_hz': 0,
            'pitch_min_hz': 0,
            'pitch_max_hz': 0,
            'pitch_range_hz': 0,
            'voiced_ratio': 0
        }
    
    def _extract_energy(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Extract energy features"""
        rms = librosa.feature.rms(y=audio_data)[0]
        
        return {
            'energy_mean': float(np.mean(rms)),
            'energy_std': float(np.std(rms)),
            'energy_min': float(np.min(rms)),
            'energy_max': float(np.max(rms)),
            'energy_dynamic_range': float(np.max(rms) - np.min(rms)),
            'energy_cv': float(np.std(rms) / np.mean(rms)) if np.mean(rms) > 0 else 0
        }
```

### 7.2 Segment Metrics (片段指标)

**文件**: `src/audio_metrics/modules/segment_metrics.py`

```python
"""
Segment Metrics Module
Extracts acoustic features for individual speech segments
"""

import numpy as np
from typing import Dict, Any, List
import librosa


class SegmentMetricsExtractor:
    """Extract metrics for each speech segment"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
    
    def extract(self, audio_data: np.ndarray, segments: List[Dict]) -> List[Dict]:
        """Extract acoustic features for each segment"""
        metrics = []
        
        for seg in segments:
            start_sample = int(seg['start'] * self.sample_rate)
            end_sample = int(seg['end'] * self.sample_rate)
            segment_audio = audio_data[start_sample:end_sample]
            
            if len(segment_audio) < 100:
                metrics.append({})
                continue
            
            # Extract features
            metric = self._extract_segment_features(segment_audio)
            metric['segment'] = seg
            metrics.append(metric)
        
        return metrics
    
    def _extract_segment_features(self, audio: np.ndarray) -> Dict[str, Any]:
        """Extract features for a single segment"""
        features = {}
        
        # Pitch
        try:
            f0, _, _ = librosa.pyin(audio, fmin=65, fmax=500, sr=self.sample_rate)
            voiced_f0 = f0[~np.isnan(f0)]
            if len(voiced_f0) > 0:
                features['pitch_mean_hz'] = float(np.mean(voiced_f0))
        except:
            pass
        
        # Energy
        rms = librosa.feature.rms(y=audio)[0]
        features['energy_mean'] = float(np.mean(rms))
        
        return features
```

---

## 8. JSON 导出模块

**文件**: `src/audio_metrics/exporters/enhanced_json_exporter.py`

```python
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
        self.output_path = output_path
    
    def export(self, audio_info: Dict, vad_analysis: Dict, transcript_result: Dict,
               prosody_metrics: Dict, emotion_metrics: Dict, filler_metrics: Dict,
               diarization_result: Dict = None, segments: List[Dict] = None,
               summary: Dict = None, keywords: Dict = None, output_path: str = None) -> str:
        """Export enriched JSON"""
        output_path = output_path or self.output_path
        
        result = self._build_enhanced_structure(
            audio_info=audio_info, vad_analysis=vad_analysis,
            transcript_result=transcript_result, prosody_metrics=prosody_metrics,
            emotion_metrics=emotion_metrics, filler_metrics=filler_metrics,
            diarization_result=diarization_result, segments=segments,
            summary=summary, keywords=keywords
        )
        
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhanced JSON exported", path=str(output_file))
            return str(output_file)
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    def _build_enhanced_structure(self, audio_info: Dict, vad_analysis: Dict,
                                   transcript_result: Dict, prosody_metrics: Dict,
                                   emotion_metrics: Dict, filler_metrics: Dict,
                                   diarization_result: Dict = None, segments: List[Dict] = None,
                                   summary: Dict = None, keywords: Dict = None) -> Dict[str, Any]:
        """Build the enhanced JSON structure"""
        
        meta = {
            "version": "2.0.0",
            "analyzer": "audio-metrics-cli",
            "timestamp": datetime.now().isoformat(),
            "file": audio_info.get("file_name", ""),
            "duration_seconds": audio_info.get("duration_seconds", 0)
        }
        
        summary_section = self._build_summary_section(
            vad_analysis=vad_analysis, transcript_result=transcript_result,
            diarization_result=diarization_result, summary=summary, keywords=keywords
        )
        
        speakers_section = self._build_speakers_section(diarization_result, vad_analysis)
        
        segments_section = segments or self._build_simple_segments(transcript_result)
        
        topics_section = self._build_topics_section(keywords)
        
        metrics_section = {
            "vad": vad_analysis,
            "prosody": prosody_metrics,
            "emotion": emotion_metrics,
            "filler_words": filler_metrics
        }
        
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
    
    def _build_speakers_section(self, diarization_result: Dict = None, vad_analysis: Dict = None) -> Dict[str, Any]:
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
```

---

## 9. requirements.txt

```txt
# Core
click>=8.0.0
tqdm>=4.62.0
numpy>=1.21.0

# Audio Processing
librosa>=0.9.0
soundfile>=0.10.0

# Speech-to-Text
openai-whisper>=20230314

# Voice Activity Detection
torch>=1.10.0
torchaudio>=0.10.0

# Speaker Diarization
pyannote.audio>=3.0.0

# Emotion Recognition (Optional)
speechbrain>=0.5.0

# Export
jsonschema>=4.0.0

# Development
pytest>=7.0.0
black>=22.0.0
ruff>=0.1.0
```

---

## 10. 示例 JSON 输出

**文件**: `outputs/test_results/enhanced_analysis_v2.json`

```json
{
  "meta": {
    "version": "2.0.0",
    "analyzer": "audio-metrics-cli",
    "timestamp": "2026-03-11T07:42:36.721871",
    "file": "meeting_sample_60s.m4a",
    "duration_seconds": 60.01
  },
  "summary": {
    "one_liner": "会议讨论：今天，明天",
    "method": "heuristic",
    "confidence": 0.5,
    "stats": {
      "speech_ratio": 0.33,
      "num_speakers": 2,
      "total_words": 202,
      "duration_seconds": 59.2
    },
    "key_topics": ["时间规划"],
    "action_items": []
  },
  "speakers": {
    "detected": true,
    "num_speakers": 2,
    "total_speech_duration": 47.62,
    "profiles": [
      {
        "id": "SPEAKER_00",
        "label": "发言人 00",
        "total_time": 46.88,
        "ratio": 0.984,
        "turn_count": 11,
        "speech_turns": 11
      },
      {
        "id": "SPEAKER_01",
        "label": "发言人 01",
        "total_time": 0.74,
        "ratio": 0.016,
        "turn_count": 1,
        "speech_turns": 1
      }
    ]
  },
  "segments": [
    {
      "start": 0.03,
      "end": 1.65,
      "speaker": "SPEAKER_00",
      "text": "我在翻譯剛出來他面嗎",
      "emotion": "neutral",
      "pitch": 331.33,
      "energy": 0.0309
    },
    {
      "start": 2.04,
      "end": 3.22,
      "speaker": "SPEAKER_00",
      "text": "現在在對路了好 行我",
      "emotion": "neutral",
      "pitch": 118.22,
      "energy": 0.028269
    }
  ],
  "topics": {
    "extracted": true,
    "keywords": [
      {"keyword": "今天", "count": 2, "positions": [29, 114]},
      {"keyword": "明天", "count": 1, "positions": [91]}
    ],
    "topics": [
      {"topic": "时间规划", "keywords": ["今天", "明天"], "mentions": 3}
    ]
  },
  "transcript": {
    "full_text": "我在翻譯剛出來他面嗎現在在對路了好...",
    "language": "zh",
    "model": "base"
  },
  "metrics": {
    "vad": {
      "speech_segments": [...],
      "speech_duration": 1.53,
      "silence_duration": 58.47,
      "speech_ratio": 0.01,
      "pause_count": 2,
      "avg_pause_duration": 1.43
    },
    "prosody": {
      "pitch_mean_hz": 122.22,
      "pitch_std_hz": 27.58,
      "energy_mean": 0.0271,
      "energy_cv": 1.067
    },
    "emotion": {
      "dominant_emotion": "neutral",
      "confidence": 0.5
    },
    "filler_words": {
      "filler_word_count": 3,
      "fillers_per_100_words": 60.0,
      "filler_by_type": {"啊": 3}
    }
  }
}
```

---

## 11. CLI 运行日志

**命令**: `audio-metrics analyze meeting_sample_60s.m4a --show-progress`

```
============================================================
Audio Metrics CLI v2.0 - Enhanced Analysis
============================================================
Input: meeting_sample_60s.m4a
Diarization: auto
Summary: heuristic

[1/9] Loading audio...
  Note: Using librosa for .m4a format
  [OK] Duration: 60.01s

[2/9] Voice activity detection...
2026-03-10T23:41:34.338226Z [info] Silero VAD model loaded from cache
  [OK] Speech ratio: 33.0%

[3/9] Speech-to-text...
2026-03-10T23:41:34.790640Z [info] Whisper model loaded device=auto model=base cache=C:\Users\clawbot\.cache\whisper
Detected language: Chinese
  [OK] Language: zh

[4/9] Prosody analysis...

[5/9] Emotion analysis...

[6/9] Filler word detection...

[7/9] Speaker diarization...
2026-03-10T23:42:03.960255Z [info] Speaker diarization model loaded on CPU
2026-03-10T23:42:18.547096Z [info] Using pyannote v4.0+ API
2026-03-10T23:42:18.547180Z [info] Diarization complete num_segments=12 num_speakers=2
  [OK] Detected 2 speakers

[8/9] Generating summary and keywords...
2026-03-10T23:42:36.721156Z [info] Summary generated by heuristic method
  [OK] Summary: heuristic
  [OK] Topics: 1

[9/9] Exporting JSON...
2026-03-10T23:42:36.722763Z [info] Enhanced JSON exported path=outputs\test_results\enhanced_analysis_v2.json

============================================================
Analysis Complete
============================================================
Duration: 60.0s
Speech ratio: 33.0%
Speakers: 2
Words: 202 chars
Summary: 会议讨论：今天，明天...
Processing time: 83.04s

[OK] Exported: outputs\test_results\enhanced_analysis_v2.json
```

---

## 附录：模型离线配置

**文件**: `src/audio_metrics/core/model_config.py`

```python
"""
Model Configuration - Centralized model loading with offline-first strategy
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from core.logger import get_logger

logger = get_logger(__name__)


class ModelConfig:
    """Centralized model configuration with offline-first strategy"""
    
    TORCH_CACHE = Path(os.path.expanduser("~/.cache/torch"))
    WHISPER_CACHE = Path(os.path.expanduser("~/.cache/whisper"))
    HUGGINGFACE_CACHE = Path(os.path.expanduser("~/.cache/huggingface"))
    
    @classmethod
    def set_offline_mode(cls):
        """Set environment variables for offline mode"""
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['TORCH_HOME'] = str(cls.TORCH_CACHE)
        logger.info("Offline mode enabled")
    
    @classmethod
    def check_silero_vad(cls) -> bool:
        """Check if Silero VAD model is cached"""
        cache_dir = cls.TORCH_CACHE / "hub" / "snakers4_silero-vad_master" / "src"
        return cache_dir.exists()
    
    @classmethod
    def check_whisper(cls, model_name: str = "base") -> bool:
        """Check if Whisper model is cached"""
        model_file = cls.WHISPER_CACHE / f"{model_name}.pt"
        return model_file.exists()
    
    @classmethod
    def check_pyannote(cls) -> bool:
        """Check if pyannote model is cached"""
        model_dir_name = "models--pyannote--speaker-diarization-3.1"
        cache_dir = cls.HUGGINGFACE_CACHE / "hub" / model_dir_name
        return cache_dir.exists()
```

---

**文档结束**
