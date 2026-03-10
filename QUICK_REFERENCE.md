# Quick Reference: Multi-Speaker Analysis

## Command Line

```bash
# Basic usage
audio-metrics analyze-multi audio.wav -o result.json

# With speaker count
audio-metrics analyze-multi audio.wav --num-speakers 2 --show-progress

# With speaker range
audio-metrics analyze-multi audio.wav --min-speakers 2 --max-speakers 5
```

## Python API

```python
from audio_metrics import run_multi_speaker_analysis
import asyncio

# Async usage
results = await run_multi_speaker_analysis("audio.wav", num_speakers=2)

# Or use individual modules
from audio_metrics import (
    SpeakerDiarization,
    TimelineBuilder,
    SpeakerMetricsAggregator
)

diarizer = SpeakerDiarization()
result = diarizer.diarize("audio.wav", num_speakers=2)
```

## Output Structure

```json
{
  "audio_info": { /* Audio metadata */ },
  "conversation_timeline": [ /* Segments */ ],
  "speaker_profiles": [ /* Per-speaker stats */ ],
  "conversation_metrics": { /* Overall dynamics */ },
  "global_acoustic_metrics": { /* Aggregate features */ },
  "processing_meta": { /* Processing info */ }
}
```

## Key Metrics

### Conversation Metrics
- `num_speakers`: Number of detected speakers
- `total_turns`: Total speech turns
- `speaker_changes`: Number of speaker switches
- `overlap_ratio`: Fraction of overlapping speech
- `mean_response_latency`: Average response time (seconds)
- `fluency_score`: 0-1, higher = smoother flow
- `engagement_score`: 0-1, higher = more interactive
- `balance_score`: 0-1, higher = more equal participation

### Speaker Profiles
- `total_speaking_time`: Total seconds spoken
- `turn_count`: Number of turns
- `avg_turn_duration`: Average turn length
- `overlap_ratio`: Fraction of overlapping turns
- `inferred_role`: dominant_speaker | active_participant | occasional_speaker | minimal_speaker
- `acoustic_profile.avg_pitch_hz`: Average pitch

## Processing Steps

1. Loading audio
2. Extracting audio metadata
3. Voice activity detection
4. Speaker diarization (pyannote.audio)
5. Building conversation timeline
6. Extracting segment acoustic metrics
7. Computing timing relations
8. Aggregating speaker metrics
9. Exporting JSON

## Requirements

```bash
pip install pyannote.audio>=3.0.0 torch>=2.0.0

# Hugging Face setup
huggingface-cli login
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Model loading failed | Run `huggingface-cli login` |
| Poor speaker separation | Use `--num-speakers 2` |
| CUDA out of memory | Run on CPU |
| pyannote not found | `pip install pyannote.audio` |

## Performance

- **CPU:** 1-2x real-time
- **GPU:** 2-3x faster than CPU
- **Memory:** 2-4GB typical
- **Accuracy:** ~85% DER

## Examples

### Interview Analysis
```bash
audio-metrics analyze-multi interview.wav \
  --num-speakers 2 \
  --output interview.json
```

### Meeting Analysis
```bash
audio-metrics analyze-multi meeting.wav \
  --min-speakers 3 --max-speakers 8 \
  --show-progress
```

### Customer Call
```bash
audio-metrics analyze-multi support_call.wav \
  --num-speakers 2 \
  --output call_analysis.json
```

---

For detailed documentation: `MULTI_SPEAKER_GUIDE.md`
