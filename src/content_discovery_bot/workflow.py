"""工作流管道 - 任务编排和调度"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from .analyzer import TopicAnalyzer
from .collector import CollectorManager
from .config import get_config
from .database import DatabaseManager
from .generator import ArticleGenerator
from .models import ArticleDraft, PipelineLogORM, RawContent, TopicAnalysis


class ContentPipeline:
    """内容工作流管道"""
    
    def __init__(self):
        self.config = get_config()
        self.collector_manager = CollectorManager()
        self.analyzer = TopicAnalyzer()
        self.generator = ArticleGenerator()
        self.db = DatabaseManager(self.config.db_path)
        self.scheduler: AsyncIOScheduler | None = None
    
    async def run_daily_workflow(self, generate_articles: bool = True) -> dict:
        """
        每日完整工作流
        
        流程：采集 -> 去重 -> 分析 -> 评分 -> 生成(可选)
        """
        start_time = datetime.utcnow()
        stats = {
            "fetched": 0,
            "deduplicated": 0,
            "analyzed": 0,
            "generated": 0,
            "errors": []
        }
        
        logger.info("=" * 50)
        logger.info("开始每日内容工作流")
        logger.info("=" * 50)
        
        try:
            # Step 1: 采集内容
            logger.info("[1/5] 采集内容...")
            all_contents = await self.collector_manager.collect_all()
            stats["fetched"] = len(all_contents)
            logger.info(f"采集完成: {len(all_contents)} 条原始内容")
            
            # Step 2: 去重
            logger.info("[2/5] 去重...")
            unique_contents = self.analyzer.deduplicate_contents(all_contents)
            stats["deduplicated"] = len(unique_contents)
            logger.info(f"去重后: {len(unique_contents)} 条")
            
            # 保存到数据库
            await self.collector_manager.save_all(unique_contents)
            
            # Step 3: 分析选题
            logger.info("[3/5] 分析选题...")
            analyses = await self.analyzer.analyze_batch(unique_contents)
            stats["analyzed"] = len(analyses)
            logger.info(f"分析完成: {len(analyses)} 条通过阈值")
            
            # 显示Top 5
            logger.info("Top 5 选题:")
            for i, a in enumerate(analyses[:5], 1):
                logger.info(f"  {i}. [{a.total_score}分] {a.suggested_angle}")
            
            # Step 4 & 5: 生成文章
            if generate_articles and analyses:
                logger.info("[4/5] 生成文章草稿...")
                generated = await self._generate_articles(analyses[:5])  # Top 5
                stats["generated"] = generated
                logger.info(f"生成完成: {generated} 篇草稿")
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            stats["errors"].append(str(e))
        
        # 记录日志
        duration = (datetime.utcnow() - start_time).total_seconds()
        await self._log_run(stats, duration)
        
        logger.info("=" * 50)
        logger.info(f"工作流完成，耗时 {duration:.1f}s")
        logger.info("=" * 50)
        
        return stats
    
    async def _generate_articles(self, analyses: List[TopicAnalysis]) -> int:
        """生成文章草稿"""
        generated = 0
        
        for analysis in analyses:
            try:
                # 决定是否用深度模式
                use_deep = self.analyzer.should_use_deep_mode(analysis)
                
                # 获取源内容
                sources = []  # 可以从数据库查询关联的RawContent
                
                if use_deep:
                    logger.info(f"使用深度模式生成: {analysis.suggested_angle}")
                    draft = await self.generator.generate_deep(analysis, sources)
                else:
                    logger.info(f"使用轻量模式生成: {analysis.suggested_angle}")
                    draft = await self.generator.generate_lightweight(analysis)
                
                # 保存草稿
                await self.generator.save_draft(draft, analysis.content_id)
                generated += 1
                
            except Exception as e:
                logger.error(f"生成文章失败 {analysis.suggested_angle}: {e}")
        
        return generated
    
    async def _log_run(self, stats: dict, duration: float) -> None:
        """记录运行日志"""
        log = PipelineLogORM(
            run_date=datetime.utcnow().strftime("%Y-%m-%d"),
            source="daily_pipeline",
            fetched_count=stats["fetched"],
            analyzed_count=stats["analyzed"],
            generated_count=stats["generated"],
            errors=str(stats["errors"]),
            duration_seconds=int(duration)
        )
        await self.db.log_pipeline_run(log)
    
    def start_scheduler(self):
        """启动定时调度器"""
        if self.scheduler is not None:
            logger.warning("调度器已在运行")
            return
        
        self.scheduler = AsyncIOScheduler(timezone=self.config.scheduler.timezone)
        
        # 解析时间 (HH:MM)
        hour, minute = self.config.scheduler.daily_run_time.split(":")
        
        self.scheduler.add_job(
            self.run_daily_workflow,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_content_pipeline',
            replace_existing=True,
            name='每日内容工作流'
        )
        
        self.scheduler.start()
        logger.info(f"定时调度器已启动，每天 {self.config.scheduler.daily_run_time} 运行")
    
    def stop_scheduler(self):
        """停止调度器"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None
            logger.info("调度器已停止")
    
    async def run_once(self, skip_generation: bool = False):
        """手动运行一次"""
        return await self.run_daily_workflow(generate_articles=not skip_generation)
    
    async def get_status(self) -> dict:
        """获取系统状态"""
        recent_logs = await self.db.get_pipeline_logs(limit=5)
        recent_drafts = await self.db.get_drafts()
        
        return {
            "scheduler_running": self.scheduler is not None and self.scheduler.running,
            "next_run": self.scheduler.get_job('daily_content_pipeline').next_run_time.isoformat() 
                       if self.scheduler and self.scheduler.get_job('daily_content_pipeline') 
                       else None,
            "recent_runs": [
                {
                    "date": log.run_date,
                    "fetched": log.fetched_count,
                    "analyzed": log.analyzed_count,
                    "generated": log.generated_count,
                    "duration": log.duration_seconds
                }
                for log in recent_logs
            ],
            "drafts_count": len(recent_drafts),
            "pending_drafts": len([d for d in recent_drafts if d.status == "pending"])
        }
