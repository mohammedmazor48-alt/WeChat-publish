"""内容采集器 - 多平台异步采集"""
from __future__ import annotations

import asyncio
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

import aiohttp
import feedparser
from loguru import logger

from .config import get_config
from .database import DatabaseManager
from .models import RawContent, RawContentORM


class ContentCollector(ABC):
    """内容采集器基类"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.config = get_config()
        self.db = DatabaseManager(self.config.db_path)
    
    @abstractmethod
    async def fetch(self) -> List[RawContent]:
        """抓取内容，子类实现"""
        pass
    
    async def fetch_with_retry(
        self, 
        url: str, 
        max_retries: int = 3,
        backoff_factor: float = 1.0
    ) -> dict:
        """带重试的HTTP请求"""
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"请求失败 ({attempt+1}/{max_retries}): {e}, {wait_time}s后重试")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"请求最终失败: {url}")
                    raise
    
    def generate_id(self, url: str) -> str:
        """生成内容唯一ID"""
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    async def save_contents(self, contents: List[RawContent]) -> int:
        """保存内容到数据库"""
        saved = 0
        for content in contents:
            try:
                await self.db.save_raw_content(content.to_orm())
                saved += 1
            except Exception as e:
                logger.warning(f"保存内容失败 {content.id}: {e}")
        return saved


class HNCollector(ContentCollector):
    """Hacker News采集器"""
    
    API_BASE = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self):
        super().__init__("hackernews")
        self.min_score = self.config.sources.hackernews.min_score
    
    async def fetch(self) -> List[RawContent]:
        """获取Top Stories"""
        logger.info("开始采集 Hacker News...")
        contents = []
        
        try:
            # 获取Top Stories ID列表
            top_stories = await self.fetch_with_retry(
                f"{self.API_BASE}/topstories.json"
            )
            
            # 获取前30条的详情
            tasks = [self.fetch_item(item_id) for item_id in top_stories[:30]]
            items = await asyncio.gather(*tasks, return_exceptions=True)
            
            for item in items:
                if isinstance(item, Exception):
                    continue
                if item and item.get("score", 0) >= self.min_score:
                    content = RawContent(
                        id=self.generate_id(item.get("url", f"hn_{item['id']}")),
                        title=item.get("title", ""),
                        content=item.get("text", ""),
                        url=item.get("url", f"https://news.ycombinator.com/item?id={item['id']}"),
                        source="hackernews",
                        source_name="Hacker News",
                        category="科技商业",
                        score=item.get("score", 0),
                        created_at=datetime.fromtimestamp(item.get("time", 0)),
                        raw_json=str(item)
                    )
                    contents.append(content)
            
            logger.info(f"HN采集完成: {len(contents)} 条")
            
        except Exception as e:
            logger.error(f"HN采集失败: {e}")
        
        return contents
    
    async def fetch_item(self, item_id: int) -> Optional[dict]:
        """获取单个item详情"""
        try:
            return await self.fetch_with_retry(
                f"{self.API_BASE}/item/{item_id}.json"
            )
        except Exception as e:
            logger.warning(f"获取item {item_id} 失败: {e}")
            return None


class RSSCollector(ContentCollector):
    """RSS采集器"""
    
    def __init__(self):
        super().__init__("rss")
        self.feeds = self.config.sources.rss.feeds
    
    async def fetch(self) -> List[RawContent]:
        """采集所有RSS源"""
        logger.info(f"开始采集 {len(self.feeds)} 个RSS源...")
        all_contents = []
        
        for feed_config in self.feeds:
            try:
                contents = await self.fetch_feed(feed_config)
                all_contents.extend(contents)
            except Exception as e:
                logger.error(f"RSS源 {feed_config.name} 采集失败: {e}")
        
        logger.info(f"RSS采集完成: {len(all_contents)} 条")
        return all_contents
    
    async def fetch_feed(self, feed_config) -> List[RawContent]:
        """采集单个RSS源"""
        # feedparser不支持异步，在线程中运行
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(
            None, 
            lambda: feedparser.parse(feed_config.url)
        )
        
        contents = []
        for entry in feed.entries[:10]:  # 只取最近10条
            content = RawContent(
                id=self.generate_id(entry.get("link", entry.get("id", ""))),
                title=entry.get("title", ""),
                content=entry.get("summary", entry.get("description", "")),
                url=entry.get("link", ""),
                source="rss",
                source_name=feed_config.name,
                category=feed_config.category,
                score=0,  # RSS没有互动数据
                created_at=self.parse_date(entry.get("published_parsed")),
                raw_json=str(entry)
            )
            contents.append(content)
        
        return contents
    
    def parse_date(self, published_parsed) -> datetime:
        """解析RSS日期"""
        if published_parsed:
            return datetime(*published_parsed[:6])
        return datetime.utcnow()


class CollectorManager:
    """采集器管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.collectors: List[ContentCollector] = []
        self._init_collectors()
    
    def _init_collectors(self):
        """初始化采集器"""
        if self.config.sources.hackernews.enabled:
            self.collectors.append(HNCollector())
        
        if self.config.sources.rss.enabled:
            self.collectors.append(RSSCollector())
        
        # Reddit需要特殊配置，暂不支持（需要API Key）
        logger.info(f"已初始化 {len(self.collectors)} 个采集器")
    
    async def collect_all(self) -> List[RawContent]:
        """采集所有源"""
        all_contents = []
        
        tasks = [collector.fetch() for collector in self.collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            collector_name = self.collectors[i].source_name
            if isinstance(result, Exception):
                logger.error(f"{collector_name} 采集失败: {result}")
            else:
                logger.info(f"{collector_name} 采集到 {len(result)} 条")
                all_contents.extend(result)
        
        return all_contents
    
    async def save_all(self, contents: List[RawContent]) -> int:
        """保存所有内容"""
        db = DatabaseManager(self.config.db_path)
        saved = 0
        for content in contents:
            try:
                await db.save_raw_content(content.to_orm())
                saved += 1
            except Exception as e:
                logger.warning(f"保存失败 {content.id}: {e}")
        return saved
