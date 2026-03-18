"""选题分析器 - LLM评估和评分"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

from simhash import Simhash
from sklearn.feature_extraction.text import TfidfVectorizer

from .config import LLMConfig, get_config
from .database import DatabaseManager
from .models import RawContent, TopicAnalysis, TopicScores, TopicAnalysisORM


class LLMClient:
    """LLM客户端封装"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider
        self.cache: Dict[str, str] = {}  # 简单缓存
    
    async def complete(self, prompt: str, max_tokens: int = None) -> str:
        """调用LLM完成文本生成"""
        # 检查缓存
        cache_key = hash(prompt) % 1000000
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.provider == "openai":
            result = await self._call_openai(prompt, max_tokens)
        elif self.provider == "anthropic":
            result = await self._call_anthropic(prompt, max_tokens)
        elif self.provider == "kimi":
            result = await self._call_kimi(prompt, max_tokens)
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")
        
        # 缓存结果
        self.cache[cache_key] = result
        return result
    
    async def _call_openai(self, prompt: str, max_tokens: int = None) -> str:
        """调用OpenAI API"""
        import openai
        client = openai.AsyncOpenAI(api_key=self.config.api_key)
        
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "你是一个专业的内容分析师，擅长评估社交媒体选题的价值。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=self.config.temperature
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str, max_tokens: int = None) -> str:
        """调用Anthropic API"""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
        
        response = await client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

    async def _call_kimi(self, prompt: str, max_tokens: int = None) -> str:
        """调用Kimi API (Moonshot AI)"""
        import openai
        
        # Kimi使用OpenAI兼容接口
        client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or "https://api.moonshot.cn/v1"
        )
        
        response = await client.chat.completions.create(
            model=self.config.model or "kimi-k2-0711-preview",
            messages=[
                {"role": "system", "content": "你是一个专业的内容分析师，擅长评估社交媒体选题的价值。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=self.config.temperature
        )
        return response.choices[0].message.content


class TopicAnalyzer:
    """选题分析器"""
    
    def __init__(self):
        self.config = get_config()
        self.llm = LLMClient(self.config.llm)
        self.db = DatabaseManager(self.config.db_path)
        self.min_score = self.config.analyzer.min_total_score
        self.deep_threshold = self.config.analyzer.deep_mode_threshold
        self.simhash_threshold = self.config.analyzer.simhash_threshold
        self.seen_hashes: set = set()
    
    def calculate_simhash(self, text: str) -> int:
        """计算文本的SimHash值"""
        return Simhash(text).value
    
    def is_duplicate(self, text: str, threshold: int = None) -> bool:
        """判断是否与已有内容重复"""
        threshold = threshold or self.simhash_threshold
        hash_value = self.calculate_simhash(text)
        
        for seen_hash in self.seen_hashes:
            # 计算汉明距离
            distance = bin(hash_value ^ seen_hash).count('1')
            if distance <= threshold:
                return True
        
        self.seen_hashes.add(hash_value)
        return False
    
    def deduplicate_contents(self, contents: List[RawContent]) -> List[RawContent]:
        """去重，保留互动数据更高的"""
        # 按互动数据排序
        sorted_contents = sorted(contents, key=lambda x: x.score, reverse=True)
        
        unique = []
        for content in sorted_contents:
            if not self.is_duplicate(content.content + content.title):
                unique.append(content)
        
        return unique
    
    def calculate_final_score(
        self, 
        llm_scores: TopicScores, 
        engagement: int,
        freshness_hours: float
    ) -> float:
        """
        计算最终评分
        公式: LLM综合分(50%) + 互动分(30%) + 时效分(20%)
        """
        # LLM分数 (满分50)
        llm_total = llm_scores.total
        llm_normalized = (llm_total / 50) * 10
        
        # 互动分数 (500互动=满分)
        engagement_score = min(engagement / 500, 1.0) * 10
        
        # 时效分数 (24小时内满分)
        freshness_score = max(0, 10 - (freshness_hours / 24))
        
        return llm_normalized * 0.5 + engagement_score * 0.3 + freshness_score * 0.2
    
    async def analyze_content(self, content: RawContent) -> Optional[TopicAnalysis]:
        """使用LLM分析单个内容"""
        # 检查是否已有分析
        existing = await self._check_existing_analysis(content.id)
        if existing:
            return existing
        
        prompt = f"""分析以下社交媒体内容，评估其作为公众号选题的潜力：

标题: {content.title}
内容: {content.content[:2000]}
平台: {content.source}
互动数据: {content.score}

请从以下维度评估（1-10分）：
1. 话题热度(heat): 是否当前热点？时效性如何？
2. 深度价值(depth): 是否有认知增量？值得深入探讨？
3. 争议性(controversy): 是否引发讨论？有不同观点？
4. 时效性(timeless): 是否长期有效？不会快速过时？
5. 中文适配(chinese_fit): 是否适合中文读者？本土化难度？

输出JSON格式：
{{
    "scores": {{"heat": 8, "depth": 7, "controversy": 6, "timeless": 5, "chinese_fit": 7}},
    "total_score": 33,
    "topic_category": "认知思维",
    "suggested_angle": "从反常识角度切入，探讨XXX",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "reasoning": "简要分析理由，100字以内"
}}

只输出JSON，不要其他内容。"""
        
        try:
            response = await self.llm.complete(prompt, max_tokens=1500)
            
            # 解析JSON
            # 去除可能的markdown代码块标记
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            data = json.loads(response)
            
            # 计算最终分数
            scores = TopicScores(**data.get("scores", {}))
            
            # 计算时效
            hours_ago = (datetime.utcnow() - content.created_at).total_seconds() / 3600
            
            final_score = self.calculate_final_score(
                scores, content.score, hours_ago
            )
            
            analysis = TopicAnalysis(
                content_id=content.id,
                scores=scores,
                total_score=int(final_score * 5),  # 转换为50分制
                topic_category=data.get("topic_category", "通用"),
                suggested_angle=data.get("suggested_angle", ""),
                keywords=data.get("keywords", []),
                reasoning=data.get("reasoning", "")
            )
            
            # 保存到数据库
            await self.db.save_analysis(analysis.to_orm())
            
            return analysis
            
        except Exception as e:
            from loguru import logger
            logger.error(f"LLM分析失败 {content.id}: {e}")
            return None
    
    async def _check_existing_analysis(self, content_id: str) -> Optional[TopicAnalysis]:
        """检查是否已有分析"""
        # 这里可以实现数据库查询缓存
        return None
    
    async def analyze_batch(
        self, 
        contents: List[RawContent],
        max_concurrent: int = 5
    ) -> List[TopicAnalysis]:
        """批量分析内容"""
        import asyncio
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_limit(content):
            async with semaphore:
                return await self.analyze_content(content)
        
        tasks = [analyze_with_limit(c) for c in contents]
        results = await asyncio.gather(*tasks)
        
        # 过滤None和低于阈值的
        valid_results = [
            r for r in results 
            if r is not None and r.total_score >= self.min_score
        ]
        
        # 按分数排序
        valid_results.sort(key=lambda x: x.total_score, reverse=True)
        
        return valid_results
    
    def should_use_deep_mode(self, analysis: TopicAnalysis) -> bool:
        """判断是否使用深度模式（LLM原生生成）"""
        conditions = [
            analysis.total_score >= self.deep_threshold,
            analysis.scores.depth >= 8,
            analysis.topic_category in ["社会观察", "商业洞察", "认知思维"],
            "争议" in analysis.suggested_angle or "反常识" in analysis.suggested_angle
        ]
        return sum(conditions) >= 2
