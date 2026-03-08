"""
Filler Word Detector Module
Detects filler words in transcribed text
"""

import re
from typing import Dict, Any, List


class FillerDetector:
    """Detect filler words in text"""
    
    # Chinese filler words
    CHINESE_FILLERS = [
        '呃',
        '嗯',
        '啊',
        '那个',
        '然后',
        '就是',
        '这个',
        '其实',
        '可能',
        '大概',
        '好像',
        '也许',
        '怎么说',
        '你知道',
        '我的意思是'
    ]
    
    # English filler words
    ENGLISH_FILLERS = [
        'um',
        'uh',
        'ah',
        'like',
        'you know',
        'sort of',
        'kind of',
        'basically',
        'actually',
        'literally',
        'i mean',
        'well'
    ]
    
    def __init__(self, language: str = 'zh'):
        """
        Initialize filler detector
        
        Args:
            language: Language code ('zh' or 'en')
        """
        self.language = language
        self.fillers = self.CHINESE_FILLERS if language == 'zh' else self.ENGLISH_FILLERS
    
    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect filler words in text
        
        Args:
            text: Input text
            
        Returns:
            Filler detection results
        """
        if not text:
            return {
                "filler_word_count": 0,
                "filler_ratio": 0,
                "filler_words": [],
                "filler_positions": []
            }
        
        # Normalize text
        text_lower = text.lower()
        words = text.split()
        total_words = len(words)
        
        # Find fillers
        found_fillers = []
        filler_positions = []
        
        for filler in self.fillers:
            # Count occurrences
            pattern = r'\b' + re.escape(filler) + r'\b' if filler.isascii() else re.escape(filler)
            matches = list(re.finditer(pattern, text_lower, re.IGNORECASE if filler.isascii() else 0))
            
            for match in matches:
                found_fillers.append(filler)
                filler_positions.append({
                    "filler": filler,
                    "start": match.start(),
                    "end": match.end(),
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        # Calculate metrics
        filler_count = len(found_fillers)
        filler_ratio = filler_count / total_words if total_words > 0 else 0
        
        # Group by filler type
        filler_by_type = {}
        for filler in found_fillers:
            filler_by_type[filler] = filler_by_type.get(filler, 0) + 1
        
        return {
            "filler_word_count": filler_count,
            "filler_ratio": round(filler_ratio, 4),
            "filler_words": found_fillers,
            "filler_positions": filler_positions,
            "filler_by_type": filler_by_type,
            "total_words": total_words,
            "fillers_per_100_words": round((filler_count / total_words) * 100, 2) if total_words > 0 else 0
        }
    
    def _get_context(
        self,
        text: str,
        start: int,
        end: int,
        context_size: int = 20
    ) -> str:
        """
        Get context around a filler word
        
        Args:
            text: Full text
            start: Start position of filler
            end: End position of filler
            context_size: Characters to include on each side
            
        Returns:
            Context string
        """
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        
        context = text[context_start:context_end]
        
        # Add ellipsis if truncated
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
        
        return context.strip()
    
    def analyze_frequency(
        self,
        text: str,
        segment_by: str = "paragraph"
    ) -> Dict[str, Any]:
        """
        Analyze filler frequency by segment
        
        Args:
            text: Input text
            segment_by: How to segment ('paragraph', 'sentence')
            
        Returns:
            Frequency analysis
        """
        if segment_by == "sentence":
            # Split by sentence
            segments = re.split(r'[.!?。！？]', text)
        else:
            # Split by paragraph
            segments = text.split('\n')
        
        # Remove empty segments
        segments = [s.strip() for s in segments if s.strip()]
        
        # Analyze each segment
        segment_analysis = []
        for i, segment in enumerate(segments):
            result = self.detect(segment)
            segment_analysis.append({
                "segment_id": i,
                "segment_length": len(segment),
                "filler_count": result["filler_word_count"],
                "filler_ratio": result["filler_ratio"]
            })
        
        # Find segments with most fillers
        top_segments = sorted(
            segment_analysis,
            key=lambda x: x["filler_count"],
            reverse=True
        )[:5]
        
        # Calculate statistics
        filler_counts = [s["filler_count"] for s in segment_analysis]
        avg_fillers_per_segment = sum(filler_counts) / len(filler_counts) if filler_counts else 0
        
        return {
            "total_segments": len(segments),
            "avg_fillers_per_segment": round(avg_fillers_per_segment, 2),
            "top_segments": top_segments,
            "segment_analysis": segment_analysis
        }
