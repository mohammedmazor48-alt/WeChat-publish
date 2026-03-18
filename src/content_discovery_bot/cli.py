"""CLI命令行界面 - Typer实现"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import load_config
from .database import DatabaseManager
from .workflow import ContentPipeline

app = typer.Typer(help="内容选题采集与公众号文章生成系统")
console = Console(highlight=False, emoji=False, legacy_windows=False)


@app.command()
def init(
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="配置文件路径")
):
    """初始化数据库和目录结构"""
    console.print("[bold blue]初始化 Content Discovery Bot...[/bold blue]")
    
    # 加载配置
    config = load_config(config_path)
    
    # 创建目录
    Path(config.data_dir).mkdir(parents=True, exist_ok=True)
    Path(config.drafts_dir).mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    async def _init():
        db = DatabaseManager(config.db_path)
        await db.init_db()
    
    asyncio.run(_init())
    
    console.print(f"[green]OK[/green] 数据目录: {config.data_dir}")
    console.print(f"[green]OK[/green] 草稿目录: {config.drafts_dir}")
    console.print(f"[green]OK[/green] 数据库: {config.db_path}")
    console.print("[bold green]初始化完成！[/bold green]")


@app.command()
def run(
    mode: str = typer.Option("full", "--mode", "-m", help="运行模式: full/collect/analyze"),
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="配置文件路径")
):
    """运行内容工作流"""
    console.print(f"[bold blue]运行工作流 (模式: {mode})...[/bold blue]")
    
    load_config(config_path)
    pipeline = ContentPipeline()
    
    async def _run():
        if mode == "collect":
            # 仅采集
            from .collector import CollectorManager
            cm = CollectorManager()
            contents = await cm.collect_all()
            saved = await cm.save_all(contents)
            console.print(f"[green]采集完成: {len(contents)} 条，保存 {saved} 条[/green]")
        
        elif mode == "analyze":
            # 分析已有内容
            from .analyzer import TopicAnalyzer
            from .database import DatabaseManager
            
            db = DatabaseManager(load_config().db_path)
            contents = await db.get_recent_contents(hours=48)
            
            analyzer = TopicAnalyzer()
            analyses = await analyzer.analyze_batch(contents)
            
            console.print(f"[green]分析完成: {len(analyses)} 条通过阈值[/green]")
            
            # 显示Top 5
            table = Table(title="Top 5 选题")
            table.add_column("排名", justify="right")
            table.add_column("分数", justify="right")
            table.add_column("类别")
            table.add_column("选题")
            
            for i, a in enumerate(analyses[:5], 1):
                table.add_row(str(i), str(a.total_score), a.topic_category, a.suggested_angle)
            
            console.print(table)
        
        else:  # full
            stats = await pipeline.run_daily_workflow()
            
            # 显示统计
            table = Table(title="工作流统计")
            table.add_column("指标")
            table.add_column("数量", justify="right")
            
            table.add_row("采集内容", str(stats["fetched"]))
            table.add_row("去重后", str(stats["deduplicated"]))
            table.add_row("通过分析", str(stats["analyzed"]))
            table.add_row("生成草稿", str(stats["generated"]))
            
            console.print(table)
            
            if stats["errors"]:
                console.print(f"[yellow]警告: {len(stats['errors'])} 个错误[/yellow]")
    
    asyncio.run(_run())


@app.command()
def schedule(
    action: str = typer.Argument(..., help="操作: start/stop/status"),
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="配置文件路径")
):
    """管理定时调度器"""
    load_config(config_path)
    pipeline = ContentPipeline()
    
    if action == "start":
        pipeline.start_scheduler()
        console.print("[green]定时调度器已启动[/green]")
        
        # 保持运行
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            pipeline.stop_scheduler()
            console.print("[yellow]调度器已停止[/yellow]")
    
    elif action == "stop":
        pipeline.stop_scheduler()
        console.print("[green]定时调度器已停止[/green]")
    
    elif action == "status":
        async def _status():
            status = await pipeline.get_status()
            
            console.print(f"调度器状态: {'[green]运行中[/green]' if status['scheduler_running'] else '[red]已停止[/red]'}")
            
            if status['next_run']:
                console.print(f"下次运行: {status['next_run']}")
            
            console.print(f"草稿总数: {status['drafts_count']}")
            console.print(f"待审核: {status['pending_drafts']}")
            
            # 显示最近运行记录
            if status['recent_runs']:
                table = Table(title="最近运行记录")
                table.add_column("日期")
                table.add_column("采集", justify="right")
                table.add_column("分析", justify="right")
                table.add_column("生成", justify="right")
                table.add_column("耗时", justify="right")
                
                for run in status['recent_runs']:
                    table.add_row(
                        run['date'],
                        str(run['fetched']),
                        str(run['analyzed']),
                        str(run['generated']),
                        f"{run['duration']}s"
                    )
                
                console.print(table)
        
        asyncio.run(_status())
    
    else:
        console.print(f"[red]未知操作: {action}[/red]")


@app.command()
def drafts(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="筛选状态: pending/reviewed/published"),
    limit: int = typer.Option(10, "--limit", "-n", help="显示数量")
):
    """查看文章草稿"""
    async def _list():
        db = DatabaseManager(load_config().db_path)
        drafts = await db.get_drafts(status=status)
        
        table = Table(title="文章草稿")
        table.add_column("ID", justify="right")
        table.add_column("标题")
        table.add_column("模式")
        table.add_column("状态")
        table.add_column("创建时间")
        
        for d in drafts[:limit]:
            table.add_row(
                str(d.id),
                d.title[:40] + "..." if len(d.title) > 40 else d.title,
                d.mode,
                d.status,
                d.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
    
    asyncio.run(_list())


@app.command()
def review(
    draft_id: int = typer.Argument(..., help="草稿ID"),
    action: str = typer.Argument(..., help="操作: approve/reject")
):
    """审核草稿"""
    async def _review():
        db = DatabaseManager(load_config().db_path)
        
        new_status = "reviewed" if action == "approve" else "rejected"
        await db.update_draft_status(draft_id, new_status)
        
        console.print(f"[green]草稿 #{draft_id} 已标记为 {new_status}[/green]")
    
    asyncio.run(_review())


@app.command()
def report(
    days: int = typer.Option(7, "--days", "-d", help="最近N天")
):
    """生成运行报告"""
    async def _report():
        db = DatabaseManager(load_config().db_path)
        logs = await db.get_pipeline_logs(limit=days)
        
        table = Table(title=f"最近{days}天运行报告")
        table.add_column("日期")
        table.add_column("源")
        table.add_column("采集", justify="right")
        table.add_column("分析", justify="right")
        table.add_column("生成", justify="right")
        table.add_column("耗时", justify="right")
        
        total_fetched = 0
        total_analyzed = 0
        total_generated = 0
        
        for log in logs:
            table.add_row(
                log.run_date,
                log.source,
                str(log.fetched_count),
                str(log.analyzed_count),
                str(log.generated_count),
                f"{log.duration_seconds}s"
            )
            total_fetched += log.fetched_count
            total_analyzed += log.analyzed_count
            total_generated += log.generated_count
        
        console.print(table)
        
        # 汇总
        console.print(f"\n[bold]汇总:[/bold]")
        console.print(f"  总采集: {total_fetched}")
        console.print(f"  总分析: {total_analyzed}")
        console.print(f"  总生成: {total_generated}")
    
    asyncio.run(_report())


@app.command()
def generate(
    topic: str = typer.Argument(..., help="选题/主题"),
    mode: str = typer.Option("lightweight", "--mode", "-m", help="生成模式: lightweight/deep"),
    category: str = typer.Option("认知思维", "--category", "-c", help="文章类别")
):
    """根据主题生成单篇文章"""
    console.print(f"[bold blue]生成文章: {topic} (模式: {mode})...[/bold blue]")
    
    async def _generate():
        from .analyzer import TopicAnalysis, TopicScores
        from .generator import ArticleGenerator
        
        # 创建临时选题分析
        analysis = TopicAnalysis(
            content_id="manual",
            scores=TopicScores(heat=8, depth=8, controversy=7, timeless=6, chinese_fit=8),
            total_score=37,
            topic_category=category,
            suggested_angle=topic,
            keywords=[],
            reasoning="手动生成的选题"
        )
        
        generator = ArticleGenerator()
        
        if mode == "deep":
            draft = await generator.generate_deep(analysis, [])
        else:
            draft = await generator.generate_lightweight(analysis)
        
        # 保存
        draft_id = await generator.save_draft(draft, 0)
        
        console.print(f"[green]OK[/green] 文章已生成: drafts/draft_{draft_id}.md")
        console.print(f"[dim]预览前500字:[/dim]")
        console.print(draft.content[:500] + "...")
    
    asyncio.run(_generate())


def main():
    app()


if __name__ == "__main__":
    main()
