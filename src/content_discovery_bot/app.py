"""Streamlit Web界面 - 选题工作台"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import streamlit as st

# 必须在其他导入之前设置页面配置
st.set_page_config(
    page_title="内容选题工作台",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

from content_discovery_bot.analyzer import TopicAnalyzer
from content_discovery_bot.config import load_config
from content_discovery_bot.database import DatabaseManager
from content_discovery_bot.workflow import ContentPipeline


def run_async(coro):
    """辅助函数：运行异步代码"""
    return asyncio.run(coro)


def init_session():
    """初始化session状态"""
    if 'config' not in st.session_state:
        st.session_state.config = load_config()
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager(st.session_state.config.db_path)


def show_today_topics():
    """今日选题页面"""
    st.header("🔥 今日推荐选题")
    
    db = st.session_state.db
    
    # 获取最近分析结果
    analyses = run_async(db.get_top_analyses(limit=20))
    
    if not analyses:
        st.info("暂无分析结果，请先运行工作流")
        return
    
    for i, analysis in enumerate(analyses, 1):
        with st.expander(
            f"{i}. {analysis.suggested_angle} (评分: {analysis.total_score})",
            expanded=(i <= 3)
        ):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**类别**: {analysis.topic_category}")
                st.write(f"**建议角度**: {analysis.suggested_angle}")
                st.write(f"**理由**: {analysis.reasoning}")
                
                # 显示评分详情
                scores = {
                    "热度": analysis.heat_score,
                    "深度": analysis.depth_score,
                    "争议": analysis.controversy_score,
                    "时效": analysis.timeless_score,
                    "适配": analysis.chinese_fit_score
                }
                st.write("**评分详情**:")
                cols = st.columns(5)
                for col, (name, score) in zip(cols, scores.items()):
                    col.metric(name, score)
            
            with col2:
                # 关键词
                if analysis.keywords:
                    st.write("**关键词**:")
                    for kw in eval(analysis.keywords):
                        st.badge(kw)
            
            with col3:
                # 操作按钮
                if st.button("📝 轻量生成", key=f"light_{analysis.id}"):
                    with st.spinner("生成中..."):
                        from content_discovery_bot.generator import ArticleGenerator
                        from content_discovery_bot.models import TopicAnalysis, TopicScores
                        
                        # 重建对象
                        ta = TopicAnalysis(
                            content_id=analysis.content_id,
                            scores=TopicScores(
                                heat=analysis.heat_score,
                                depth=analysis.depth_score,
                                controversy=analysis.controversy_score,
                                timeless=analysis.timeless_score,
                                chinese_fit=analysis.chinese_fit_score
                            ),
                            total_score=analysis.total_score,
                            topic_category=analysis.topic_category,
                            suggested_angle=analysis.suggested_angle,
                            keywords=eval(analysis.keywords),
                            reasoning=analysis.reasoning
                        )
                        
                        gen = ArticleGenerator()
                        draft = run_async(gen.generate_lightweight(ta))
                        draft_id = run_async(gen.save_draft(draft, analysis.id))
                        
                        st.success(f"已生成草稿 #{draft_id}")
                        st.rerun()
                
                if st.button("🧠 深度生成", key=f"deep_{analysis.id}"):
                    with st.spinner("生成中..."):
                        from content_discovery_bot.generator import ArticleGenerator
                        from content_discovery_bot.models import TopicAnalysis, TopicScores
                        
                        ta = TopicAnalysis(
                            content_id=analysis.content_id,
                            scores=TopicScores(
                                heat=analysis.heat_score,
                                depth=analysis.depth_score,
                                controversy=analysis.controversy_score,
                                timeless=analysis.timeless_score,
                                chinese_fit=analysis.chinese_fit_score
                            ),
                            total_score=analysis.total_score,
                            topic_category=analysis.topic_category,
                            suggested_angle=analysis.suggested_angle,
                            keywords=eval(analysis.keywords),
                            reasoning=analysis.reasoning
                        )
                        
                        gen = ArticleGenerator()
                        draft = run_async(gen.generate_deep(ta, []))
                        draft_id = run_async(gen.save_draft(draft, analysis.id))
                        
                        st.success(f"已生成草稿 #{draft_id}")
                        st.rerun()


def show_draft_management():
    """草稿管理页面"""
    st.header("📝 草稿管理")
    
    db = st.session_state.db
    drafts = run_async(db.get_drafts())
    
    if not drafts:
        st.info("暂无草稿")
        return
    
    # 筛选
    status_filter = st.selectbox(
        "筛选状态",
        ["全部", "pending", "reviewed", "published", "rejected"]
    )
    
    filtered = drafts
    if status_filter != "全部":
        filtered = [d for d in drafts if d.status == status_filter]
    
    for draft in filtered:
        with st.expander(f"#{draft.id} {draft.title} [{draft.mode}] - {draft.status}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(draft.content[:1000] + "...")
                
                if st.checkbox("查看完整内容", key=f"view_{draft.id}"):
                    st.markdown(draft.content)
            
            with col2:
                st.write(f"**模式**: {draft.mode}")
                st.write(f"**状态**: {draft.status}")
                st.write(f"**创建**: {draft.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                if draft.status == "pending":
                    if st.button("✅ 通过", key=f"approve_{draft.id}"):
                        run_async(db.update_draft_status(draft.id, "reviewed"))
                        st.success("已审核通过")
                        st.rerun()
                    
                    if st.button("❌ 拒绝", key=f"reject_{draft.id}"):
                        run_async(db.update_draft_status(draft.id, "rejected"))
                        st.success("已拒绝")
                        st.rerun()
                
                # 下载按钮
                st.download_button(
                    "📥 下载Markdown",
                    draft.content,
                    file_name=f"draft_{draft.id}.md",
                    mime="text/markdown",
                    key=f"download_{draft.id}"
                )


def show_source_config():
    """源配置页面"""
    st.header("⚙️ 数据源配置")
    
    config = st.session_state.config
    
    # Reddit配置
    st.subheader("Reddit")
    st.json({
        "enabled": config.sources.reddit.enabled,
        "subreddits": [
            {"name": s.name, "min_score": s.min_score, "category": s.category}
            for s in config.sources.reddit.subreddits
        ]
    })
    
    # HN配置
    st.subheader("Hacker News")
    st.json({
        "enabled": config.sources.hackernews.enabled,
        "min_score": config.sources.hackernews.min_score
    })
    
    # RSS配置
    st.subheader("RSS订阅")
    st.json({
        "enabled": config.sources.rss.enabled,
        "feeds": [
            {"name": f.name, "category": f.category}
            for f in config.sources.rss.feeds
        ]
    })
    
    # 分析器配置
    st.subheader("分析器配置")
    st.json({
        "min_total_score": config.analyzer.min_total_score,
        "deep_mode_threshold": config.analyzer.deep_mode_threshold,
        "simhash_threshold": config.analyzer.simhash_threshold
    })


def show_logs():
    """运行日志页面"""
    st.header("📊 运行日志")
    
    db = st.session_state.db
    logs = run_async(db.get_pipeline_logs(limit=20))
    
    if not logs:
        st.info("暂无日志记录")
        return
    
    # 统计图表
    import pandas as pd
    
    df = pd.DataFrame([
        {
            "日期": log.run_date,
            "采集": log.fetched_count,
            "分析": log.analyzed_count,
            "生成": log.generated_count,
            "耗时": log.duration_seconds
        }
        for log in logs
    ])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("总采集", df["采集"].sum())
    col2.metric("总分析", df["分析"].sum())
    col3.metric("总生成", df["生成"].sum())
    
    # 趋势图
    st.subheader("采集趋势")
    st.line_chart(df.set_index("日期")[["采集", "分析", "生成"]])
    
    # 详细日志表
    st.subheader("详细日志")
    st.dataframe(df, use_container_width=True)


def show_quick_actions():
    """快速操作侧边栏"""
    st.sidebar.header("⚡ 快速操作")
    
    if st.sidebar.button("🚀 立即运行工作流"):
        with st.spinner("工作流运行中..."):
            pipeline = ContentPipeline()
            stats = run_async(pipeline.run_once())
            
            st.sidebar.success(f"完成! 采集{stats['fetched']}条, 分析{stats['analyzed']}条, 生成{stats['generated']}篇")
            st.rerun()
    
    if st.sidebar.button("🔍 仅采集内容"):
        with st.spinner("采集中..."):
            from content_discovery_bot.collector import CollectorManager
            cm = CollectorManager()
            contents = run_async(cm.collect_all())
            saved = run_async(cm.save_all(contents))
            st.sidebar.success(f"采集{len(contents)}条, 保存{saved}条")
            st.rerun()
    
    st.sidebar.divider()
    
    # 手动生成
    st.sidebar.subheader("手动生成文章")
    topic = st.sidebar.text_input("主题")
    category = st.sidebar.selectbox("类别", ["认知思维", "职场工作", "社会观察", "商业洞察"])
    mode = st.sidebar.radio("模式", ["lightweight", "deep"])
    
    if st.sidebar.button("生成") and topic:
        with st.spinner("生成中..."):
            from content_discovery_bot.analyzer import TopicAnalysis, TopicScores
            from content_discovery_bot.generator import ArticleGenerator
            
            analysis = TopicAnalysis(
                content_id="manual",
                scores=TopicScores(heat=8, depth=8, controversy=7, timeless=6, chinese_fit=8),
                total_score=37,
                topic_category=category,
                suggested_angle=topic,
                keywords=[],
                reasoning="手动生成"
            )
            
            gen = ArticleGenerator()
            if mode == "deep":
                draft = run_async(gen.generate_deep(analysis, []))
            else:
                draft = run_async(gen.generate_lightweight(analysis))
            
            draft_id = run_async(gen.save_draft(draft, 0))
            st.sidebar.success(f"已生成草稿 #{draft_id}")


def main():
    """主函数"""
    st.title("📚 内容选题工作台")
    st.caption("社媒爆款选题采集与公众号文章生成系统")
    
    # 初始化
    init_session()
    
    # 快速操作
    show_quick_actions()
    
    # 导航
    page = st.sidebar.radio(
        "导航",
        ["今日选题", "草稿管理", "源配置", "运行日志"]
    )
    
    # 显示对应页面
    if page == "今日选题":
        show_today_topics()
    elif page == "草稿管理":
        show_draft_management()
    elif page == "源配置":
        show_source_config()
    elif page == "运行日志":
        show_logs()


if __name__ == "__main__":
    main()
