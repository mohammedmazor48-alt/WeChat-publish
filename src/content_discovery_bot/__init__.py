"""Content Discovery Bot - 社媒爆款选题采集与公众号文章生成系统"""
from __future__ import annotations

__version__ = "1.0.0"
__author__ = "深蓝"

from .collector import CollectorManager, ContentCollector, HNCollector, RSSCollector
from .analyzer import TopicAnalyzer, LLMClient
from .generator import ArticleGenerator, StyleDNA
from .workflow import ContentPipeline
from .database import DatabaseManager
from .models import RawContent, TopicAnalysis, ArticleDraft
from .config import load_config, get_config

__all__ = [
    "CollectorManager",
    "ContentCollector",
    "HNCollector",
    "RSSCollector",
    "TopicAnalyzer",
    "LLMClient",
    "ArticleGenerator",
    "StyleDNA",
    "ContentPipeline",
    "DatabaseManager",
    "RawContent",
    "TopicAnalysis",
    "ArticleDraft",
    "load_config",
    "get_config",
]
