"""数据模型定义 - Pydantic + SQLAlchemy"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── SQLAlchemy ORM 模型 ──────────────────────────────────────────────────────

class RawContentORM(Base):
    __tablename__ = "raw_contents"

    id = Column(String, primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    url = Column(Text)
    source = Column(String, nullable=False)   # reddit / hackernews / rss
    source_name = Column(String)
    category = Column(String)
    score = Column(Integer, default=0)
    created_at = Column(DateTime)
    fetched_at = Column(DateTime, default=func.now())
    simhash = Column(Integer)
    raw_json = Column(Text)

    analyses = relationship("TopicAnalysisORM", back_populates="raw_content")


class TopicAnalysisORM(Base):
    __tablename__ = "topic_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String, ForeignKey("raw_contents.id"))
    total_score = Column(Integer)
    heat_score = Column(Integer)
    depth_score = Column(Integer)
    controversy_score = Column(Integer)
    timeless_score = Column(Integer)
    chinese_fit_score = Column(Integer)
    topic_category = Column(String)
    suggested_angle = Column(Text)
    keywords = Column(Text)   # JSON array
    reasoning = Column(Text)
    analyzed_at = Column(DateTime, default=func.now())

    raw_content = relationship("RawContentORM", back_populates="analyses")
    drafts = relationship("ArticleDraftORM", back_populates="analysis")


class ArticleDraftORM(Base):
    __tablename__ = "article_drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_analysis_id = Column(Integer, ForeignKey("topic_analyses.id"))
    title = Column(Text)
    content = Column(Text)
    mode = Column(String)   # lightweight / deep
    status = Column(String, default="pending")  # pending/reviewed/published/rejected
    created_at = Column(DateTime, default=func.now())
    reviewed_at = Column(DateTime)
    published_at = Column(DateTime)

    analysis = relationship("TopicAnalysisORM", back_populates="drafts")


# ── Pydantic 数据传输模型 ────────────────────────────────────────────────────

class RawContent(BaseModel):
    id: str
    title: str
    content: str = ""
    url: str = ""
    source: str
    source_name: str = ""
    category: str = "通用"
    score: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    raw_json: str = ""

    def to_orm(self) -> RawContentORM:
        return RawContentORM(
            id=self.id,
            title=self.title,
            content=self.content,
            url=self.url,
            source=self.source,
            source_name=self.source_name,
            category=self.category,
            score=self.score,
            created_at=self.created_at,
            raw_json=self.raw_json,
        )


class TopicScores(BaseModel):
    heat: int = 0
    depth: int = 0
    controversy: int = 0
    timeless: int = 0
    chinese_fit: int = 0

    @property
    def total(self) -> int:
        return sum([self.heat, self.depth, self.controversy, self.timeless, self.chinese_fit])


class TopicAnalysis(BaseModel):
    content_id: str
    scores: TopicScores
    total_score: int
    topic_category: str
    suggested_angle: str
    keywords: list[str] = Field(default_factory=list)
    reasoning: str = ""

    @classmethod
    def from_llm_json(cls, content_id: str, data: dict) -> "TopicAnalysis":
        scores_raw = data.get("scores", {})
        scores = TopicScores(**scores_raw)
        return cls(
            content_id=content_id,
            scores=scores,
            total_score=data.get("total_score", scores.total),
            topic_category=data.get("topic_category", "通用"),
            suggested_angle=data.get("suggested_angle", ""),
            keywords=data.get("keywords", []),
            reasoning=data.get("reasoning", ""),
        )

    def to_orm(self) -> TopicAnalysisORM:
        return TopicAnalysisORM(
            content_id=self.content_id,
            total_score=self.total_score,
            heat_score=self.scores.heat,
            depth_score=self.scores.depth,
            controversy_score=self.scores.controversy,
            timeless_score=self.scores.timeless,
            chinese_fit_score=self.scores.chinese_fit,
            topic_category=self.topic_category,
            suggested_angle=self.suggested_angle,
            keywords=json.dumps(self.keywords, ensure_ascii=False),
            reasoning=self.reasoning,
        )


class ArticleDraft(BaseModel):
    topic_analysis_id: Optional[int] = None
    title: str = ""
    content: str
    mode: str = "lightweight"  # lightweight / deep
    status: str = "pending"

    def to_orm(self) -> ArticleDraftORM:
        return ArticleDraftORM(
            topic_analysis_id=self.topic_analysis_id,
            title=self.title,
            content=self.content,
            mode=self.mode,
            status=self.status,
        )


class PipelineLogORM(Base):
    __tablename__ = "pipeline_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_date = Column(String)
    source = Column(String)
    fetched_count = Column(Integer, default=0)
    analyzed_count = Column(Integer, default=0)
    generated_count = Column(Integer, default=0)
    errors = Column(Text)   # JSON array
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=func.now())
