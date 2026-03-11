"""
Keyword Extractor Module
Extracts key topics and action items from transcript
"""

import re
from typing import Dict, Any, List
from collections import Counter

from core.logger import get_logger

logger = get_logger(__name__)


class KeywordExtractor:
    """Extract keywords, topics, and action items from transcript"""
    
    def __init__(self, language: str = "zh"):
        """
        Initialize extractor
        
        Args:
            language: Language code (zh|en)
        """
        self.language = language
        self.chinese_keywords = [
            "周报", "日报", "月报", "季报", "年报",
            "项目", "进度", "计划", "安排", "任务",
            "人员", "团队", "招聘", "面试",
            "开发", "测试", "产品", "设计", "技术",
            "会议", "讨论", "决定", "需要", "必须",
            "今天", "明天", "后天", "本周", "下周", "本月",
            "问题", "解决", "完成", "开始", "结束",
            "预算", "成本", "收入", "销售", "客户",
            "培训", "学习", "分享", "文档"
        ]
        
        self.action_patterns = [
            r"需要 (.+?)[,.。]",
            r"要 (.+?)[,.。]",
            r"必须 (.+?)[,.。]",
            r"记得 (.+?)[,.。]",
            r"别忘了 (.+?)[,.。]",
            r"今天 (.+?)[,.。]",
            r"明天 (.+?)[,.。]",
            r"下周 (.+?)[,.。]",
        ]
    
    def extract(self, transcript: str, segments: List[Dict] = None) -> Dict[str, Any]:
        """
        Extract keywords and action items
        
        Args:
            transcript: Full transcript text
            segments: Optional segmented transcript with timestamps
            
        Returns:
            Dict with keywords, topics, action_items
        """
        keywords = self._extract_keywords(transcript)
        topics = self._group_topics(keywords)
        action_items = self._extract_action_items(transcript, segments)
        
        return {
            "keywords": keywords,
            "topics": topics,
            "action_items": action_items
        }
    
    def _extract_keywords(self, transcript: str) -> List[Dict[str, Any]]:
        """Extract keywords with frequency and positions"""
        keyword_matches = {}
        
        for kw in self.chinese_keywords:
            positions = []
            start = 0
            while True:
                pos = transcript.find(kw, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + len(kw)
            
            if positions:
                keyword_matches[kw] = {
                    "keyword": kw,
                    "count": len(positions),
                    "positions": positions[:10]  # Limit to first 10
                }
        
        # Sort by frequency
        sorted_keywords = sorted(
            keyword_matches.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        return sorted_keywords[:20]  # Top 20
    
    def _group_topics(self, keywords: List[Dict]) -> List[Dict[str, Any]]:
        """Group keywords into topics"""
        topic_groups = {
            "工作报告": ["周报", "日报", "月报", "季报", "年报"],
            "项目管理": ["项目", "进度", "计划", "安排", "任务"],
            "人员团队": ["人员", "团队", "招聘", "面试"],
            "技术开发": ["开发", "测试", "产品", "设计", "技术"],
            "会议决策": ["会议", "讨论", "决定", "需要", "必须"],
            "时间规划": ["今天", "明天", "后天", "本周", "下周", "本月"]
        }
        
        topics = []
        for topic_name, topic_keywords in topic_groups.items():
            matched = [kw for kw in keywords if kw["keyword"] in topic_keywords]
            if matched:
                total_mentions = sum(kw["count"] for kw in matched)
                topics.append({
                    "topic": topic_name,
                    "keywords": [kw["keyword"] for kw in matched],
                    "mentions": total_mentions
                })
        
        # Sort by mentions
        topics.sort(key=lambda x: x["mentions"], reverse=True)
        
        return topics
    
    def _extract_action_items(self, transcript: str, segments: List[Dict] = None) -> List[Dict[str, Any]]:
        """Extract action items from transcript"""
        action_items = []
        
        for pattern in self.action_patterns:
            matches = re.finditer(pattern, transcript)
            for match in matches:
                action_text = match.group(1).strip()
                
                # Find timestamp if segments available
                timestamp = None
                if segments:
                    for seg in segments:
                        if match.start() >= seg.get("start", 0) and match.end() <= seg.get("end", 0):
                            timestamp = seg.get("start")
                            break
                
                # Filter out very short or very long actions
                if 2 <= len(action_text) <= 50:
                    action_items.append({
                        "action": action_text,
                        "timestamp": timestamp,
                        "pattern": pattern
                    })
        
        # Remove duplicates (keep unique actions)
        seen = set()
        unique_actions = []
        for item in action_items:
            if item["action"] not in seen:
                seen.add(item["action"])
                unique_actions.append(item)
        
        return unique_actions[:10]  # Top 10
