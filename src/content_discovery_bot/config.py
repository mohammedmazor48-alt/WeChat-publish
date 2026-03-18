"""配置加载模块"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


def _expand_env_vars(value: Any) -> Any:
    """递归展开配置中的环境变量占位符 ${VAR_NAME}"""
    if isinstance(value, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: os.getenv(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(i) for i in value]
    return value


class SubredditConfig(BaseModel):
    name: str
    min_score: int = 100
    category: str = "通用"
    check_interval_hours: int = 6


class RedditConfig(BaseModel):
    enabled: bool = True
    client_id: str = ""
    client_secret: str = ""
    subreddits: list[SubredditConfig] = Field(default_factory=list)


class HNConfig(BaseModel):
    enabled: bool = True
    min_score: int = 100
    check_interval_hours: int = 6


class RSSFeedConfig(BaseModel):
    name: str
    url: str
    category: str = "通用"
    check_interval_hours: int = 12


class RSSConfig(BaseModel):
    enabled: bool = True
    feeds: list[RSSFeedConfig] = Field(default_factory=list)


class SourcesConfig(BaseModel):
    reddit: RedditConfig = Field(default_factory=RedditConfig)
    hackernews: HNConfig = Field(default_factory=HNConfig)
    rss: RSSConfig = Field(default_factory=RSSConfig)


class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key: str = ""
    max_tokens: int = 4000
    temperature: float = 0.7


class AnalyzerConfig(BaseModel):
    simhash_threshold: int = 3
    min_total_score: int = 25
    deep_mode_threshold: int = 35


class GeneratorConfig(BaseModel):
    style_dna_path: str = "references/style-dna.md"
    output_format: str = "markdown"


class SchedulerConfig(BaseModel):
    daily_run_time: str = "08:00"
    timezone: str = "Asia/Shanghai"


class NotificationsConfig(BaseModel):
    enabled: bool = False
    type: str = "discord"
    webhook_url: str = ""


class AppConfig(BaseModel):
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    analyzer: AnalyzerConfig = Field(default_factory=AnalyzerConfig)
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    data_dir: str = "./data"
    drafts_dir: str = "./drafts"
    db_path: str = "./data/content_discovery.db"


_config: AppConfig | None = None


def load_config(config_path: str | Path = "config.yaml") -> AppConfig:
    global _config
    path = Path(config_path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        raw = _expand_env_vars(raw)
        system = raw.pop("system", {})
        database = raw.pop("database", {})
        raw["data_dir"] = system.get("data_dir", "./data")
        raw["drafts_dir"] = system.get("drafts_dir", "./drafts")
        raw["db_path"] = database.get("path", "./data/content_discovery.db")
        _config = AppConfig(**raw)
    else:
        _config = AppConfig()
    # Ensure directories exist
    Path(_config.data_dir).mkdir(parents=True, exist_ok=True)
    Path(_config.drafts_dir).mkdir(parents=True, exist_ok=True)
    return _config


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config
