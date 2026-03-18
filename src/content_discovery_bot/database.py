"""数据库管理器 - 异步SQLAlchemy + SQLite"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import (
    ArticleDraftORM, Base, PipelineLogORM, RawContentORM, TopicAnalysisORM,
)


class DatabaseManager:
    def __init__(self, db_path: str = "./data/content_discovery.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite+aiosqlite:///{db_path}"
        self._engine = create_async_engine(url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库初始化完成")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    async def save_raw_content(self, content_orm: RawContentORM) -> None:
        from sqlalchemy import select
        async with self.session() as s:
            existing = await s.get(RawContentORM, content_orm.id)
            if existing is None:
                s.add(content_orm)

    async def save_raw_contents(self, contents: list[RawContentORM]) -> int:
        saved = 0
        for c in contents:
            async with self.session() as s:
                existing = await s.get(RawContentORM, c.id)
                if existing is None:
                    s.add(c)
                    saved += 1
        return saved

    async def save_analysis(self, analysis_orm: TopicAnalysisORM) -> int:
        async with self.session() as s:
            s.add(analysis_orm)
            await s.flush()
            return analysis_orm.id

    async def save_draft(self, draft_orm: ArticleDraftORM) -> int:
        async with self.session() as s:
            s.add(draft_orm)
            await s.flush()
            return draft_orm.id

    async def get_recent_contents(self, hours: int = 24) -> list[RawContentORM]:
        from datetime import datetime, timedelta
        from sqlalchemy import select
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        async with self.session() as s:
            result = await s.execute(
                select(RawContentORM).where(RawContentORM.fetched_at >= cutoff)
            )
            return list(result.scalars().all())

    async def get_top_analyses(self, limit: int = 10) -> list[TopicAnalysisORM]:
        from sqlalchemy import select
        async with self.session() as s:
            result = await s.execute(
                select(TopicAnalysisORM)
                .order_by(TopicAnalysisORM.total_score.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_drafts(self, status: str | None = None) -> list[ArticleDraftORM]:
        from sqlalchemy import select
        async with self.session() as s:
            q = select(ArticleDraftORM).order_by(ArticleDraftORM.created_at.desc())
            if status:
                q = q.where(ArticleDraftORM.status == status)
            result = await s.execute(q)
            return list(result.scalars().all())

    async def update_draft_status(self, draft_id: int, status: str) -> None:
        from datetime import datetime
        async with self.session() as s:
            draft = await s.get(ArticleDraftORM, draft_id)
            if draft:
                draft.status = status
                if status == "reviewed":
                    draft.reviewed_at = datetime.utcnow()
                elif status == "published":
                    draft.published_at = datetime.utcnow()

    async def log_pipeline_run(self, log_orm: PipelineLogORM) -> None:
        async with self.session() as s:
            s.add(log_orm)

    async def get_pipeline_logs(self, limit: int = 20) -> list[PipelineLogORM]:
        from sqlalchemy import select
        async with self.session() as s:
            result = await s.execute(
                select(PipelineLogORM)
                .order_by(PipelineLogORM.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
