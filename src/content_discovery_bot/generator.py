"""文章生成器 - 轻量/深度模式"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

from loguru import logger

from .config import get_config
from .database import DatabaseManager
from .models import ArticleDraft, ArticleDraftORM, RawContent, TopicAnalysis


class StyleDNA:
    """风格DNA加载器"""
    
    def __init__(self, dna_path: str):
        self.path = Path(dna_path)
        self.content = self._load()
    
    def _load(self) -> str:
        """加载风格DNA文件"""
        if self.path.exists():
            return self.path.read_text(encoding="utf-8")
        return self._default_dna()
    
    def _default_dna(self) -> str:
        """默认风格DNA"""
        return """
        写作风格：理性说书人，用理工科思维分析人文话题
        语言特点：口语化书面语，长短句交错，善用破折号
        结构模式：故事开场 → 问题提出 → 多角度分析 → 反常识观点 → 金句结尾
        人称使用：第一人称"我" + 第二人称"你"
        """
    
    def get_prompt_for_category(self, category: str) -> str:
        """获取特定类别的风格提示"""
        templates = {
            "认知思维": """
                用认知思维类风格写作：
                - 多引用心理学实验、脑科学研究
                - 使用类比解释抽象概念
                - 保持理性客观，适度幽默
                - 结构清晰，层层递进
            """,
            "职场工作": """
                用职场工作类风格写作：
                - 从宏观历史角度切入
                - 使用数据支撑观点
                - 平衡批判性和建设性
                - 提供可操作建议
            """,
            "社会观察": """
                用社会观察类风格写作：
                - 多视角呈现事件
                - 历史对照增加深度
                - 系统性思考替代情绪化
                - 保持人文关怀
            """
        }
        return templates.get(category, "保持深蓝一贯的写作风格")


class ArticleGenerator:
    """文章生成器"""
    
    def __init__(self):
        self.config = get_config()
        self.style_dna = StyleDNA(self.config.generator.style_dna_path)
        self.db = DatabaseManager(self.config.db_path)
    
    async def generate_lightweight(self, topic: TopicAnalysis) -> ArticleDraft:
        """
        轻量模式生成 - 模板填充
        适合常规选题，成本低
        """
        from .analyzer import LLMClient
        
        llm = LLMClient(self.config.llm)
        
        style_prompt = self.style_dna.get_prompt_for_category(topic.topic_category)
        
        prompt = f"""根据以下选题信息，撰写一篇公众号文章（轻量模式）。

{style_prompt}

选题信息：
- 标题：{topic.suggested_angle}
- 类别：{topic.topic_category}
- 切入角度：{topic.suggested_angle}
- 关键词：{', '.join(topic.keywords)}

要求：
1. 字数：1500-2000字
2. 结构：故事开场(200字) → 问题分析(600字) → 观点阐述(600字) → 建议总结(300字) → 金句结尾(100字)
3. 语气：理性但温暖，像朋友聊天
4. 必须包含：一个具体故事/案例、一个反常识观点、可落地的建议

直接输出Markdown格式文章，不需要标题以外的其他说明。"""
        
        content = await llm.complete(prompt, max_tokens=3000)
        
        return ArticleDraft(
            topic_analysis_id=None,  # 稍后关联
            title=topic.suggested_angle,
            content=content,
            mode="lightweight"
        )
    
    async def generate_deep(
        self, 
        topic: TopicAnalysis, 
        sources: List[RawContent]
    ) -> ArticleDraft:
        """
        深度模式生成 - LLM原生
        适合重要选题，质量高
        """
        from .analyzer import LLMClient
        
        llm = LLMClient(self.config.llm)
        
        # 格式化参考资料
        sources_text = "\n\n".join([
            f"来源{i+1}: {s.title}\n{s.content[:800]}"
            for i, s in enumerate(sources[:3])  # 最多3个来源
        ])
        
        style_prompt = self.style_dna.get_prompt_for_category(topic.topic_category)
        
        prompt = f"""你是资深公众号作者"深蓝"，请根据以下选题和参考资料，撰写一篇深度文章。

【风格要求】
{style_prompt}

【选题信息】
- 建议标题：{topic.suggested_angle}
- 切入角度：{topic.suggested_angle}
- 话题类别：{topic.topic_category}
- 目标字数：1800-2500字

【参考资料】
{sources_text}

【文章结构要求】
1. 故事开场 (150-250字)：引人入胜的具体故事或场景
2. 问题提出 (200-300字)：明确核心矛盾和读者痛点
3. 背景分析 (400-500字)：多角度分析，引用参考资料
4. 反常识观点 (400-500字)：制造认知冲突，挑战直觉
5. 深度解读 (400-500字)：系统思考，揭示底层逻辑
6. 行动建议 (200-300字)：可落地的具体方法
7. 金句结尾 (100-150字)：memorable，引发思考

【写作原则】
- 用第一人称"我"，像和读者对话
- 善用破折号——制造停顿和思考
- 段落不要太长，适合手机阅读
- 重要观点加粗强调
- 避免过度鸡汤，保持理性底色

直接输出完整的Markdown格式文章。"""
        
        content = await llm.complete(prompt, max_tokens=4000)
        
        return ArticleDraft(
            topic_analysis_id=None,
            title=topic.suggested_angle,
            content=content,
            mode="deep",
            sources=[s.id for s in sources]
        )
    
    async def generate_via_wechat_skill(self, topic: TopicAnalysis) -> str:
        """
        调用wechat-article skill生成
        需要OpenClaw环境
        """
        try:
            cmd = [
                "openclaw", "skill", "wechat-article", "run",
                "--topic", topic.suggested_angle,
                "--style", topic.topic_category,
                "--output", f"./drafts/skill_{topic.content_id}.md"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info(f"wechat-article skill 调用成功: {topic.suggested_angle}")
                return result.stdout
            else:
                logger.error(f"wechat-article skill 失败: {result.stderr}")
                return ""
                
        except Exception as e:
            logger.error(f"调用wechat-article skill失败: {e}")
            return ""
    
    async def save_draft(
        self, 
        draft: ArticleDraft, 
        analysis_id: int
    ) -> int:
        """保存草稿到数据库"""
        draft.topic_analysis_id = analysis_id
        draft_id = await self.db.save_draft(draft.to_orm())
        
        # 同时保存到文件
        draft_path = Path(self.config.drafts_dir) / f"draft_{draft_id}.md"
        draft_path.write_text(
            f"# {draft.title}\n\n{draft.content}", 
            encoding="utf-8"
        )
        
        logger.info(f"草稿已保存: {draft_path}")
        return draft_id
