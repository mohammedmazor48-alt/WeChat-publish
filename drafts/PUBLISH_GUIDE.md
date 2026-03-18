# 公众号文章发布指南

## 文章信息

| 项目 | 内容 |
|------|------|
| **标题** | 信任是场无限游戏，而我们都在透支未来 |
| **副标题** | 从学术期刊300年演化史说起 |
| **作者** | 深蓝 |
| **字数** | 约 3,200 字 |
| **摘要** | 从学术期刊300年演化史说起：100次履约建立的信任，1次违约就能归零。 |

## 文件位置

- **Markdown原文**: `D:\tools\content-discovery-bot\drafts\信任是场无限游戏.md`
- **HTML格式**: `D:\tools\content-discovery-bot\drafts\article_trust.html`
- **封面设计**: `D:\tools\content-discovery-bot\drafts\cover_design.md`

## 手动发布步骤

### 方法一：复制粘贴（推荐）

1. 打开 `信任是场无限游戏.md` 文件
2. 复制全部内容
3. 登录微信公众号后台：https://mp.weixin.qq.com
4. 进入「内容管理」→「新建图文」
5. 粘贴内容，调整格式
6. 上传封面图（建议尺寸 900×383）
7. 保存并群发

### 方法二：使用 wechat-article skill（需本地环境）

```bash
cd D:\tools\content-discovery-bot

# 安装依赖（如果尚未安装）
pip install -r requirements.txt

# 生成封面图
python -c "
from src.content_discovery_bot.generator import StyleDNA
# 封面生成代码...
"

# 推送草稿
python scripts/publish_draft.py \
  --title "信任是场无限游戏，而我们都在透支未来" \
  --author "深蓝" \
  --digest "从学术期刊300年演化史说起：100次履约建立的信任，1次违约就能归零。" \
  --content-file drafts/article_trust.html \
  --appid wx136c36b5d8a7d3bc \
  --appsecret cbfa6c8502e20e0e5dd935d5f7e2e80a \
  --need-open-comment 1 \
  --only-fans-can-comment 0
```

## 封面图建议

由于没有成功生成封面图，建议：

1. **使用在线工具生成**
   - Canva (canva.com)
   - 稿定设计 (gaoding.com)
   - 创客贴 (chuangkit.com)

2. **封面设计要点**
   - 尺寸：900 × 383 像素
   - 风格：深蓝背景 + 金色点缀
   - 标题：信任是场无限游戏
   - 副标题：从学术期刊300年演化史说起

3. **配色方案**
   - 主色：#1a237e（深蓝）
   - 辅色：#ffd700（金色）
   - 文字：#ffffff（白色）

## 发布后检查清单

- [ ] 标题完整显示（不超过20字）
- [ ] 摘要清晰（120字内）
- [ ] 封面图已上传
- [ ] 作者设置为"深蓝"
- [ ] 原文链接（如有）
- [ ] 评论功能已开启
- [ ] 预览无误
- [ ] 保存到草稿箱
- [ ] 群发/定时发布

## 文章亮点

1. **个人经历切入**：土木工程项目查资料的真实故事
2. **权威历史数据**：
   - 1665年《哲学汇刊》创刊
   - 1869年《自然》杂志创办
   - 1955年影响因子诞生
3. **三大出版商数据**：
   - RELX/Elsevier：利润率37%
   - Springer Nature
   - John Wiley & Sons
4. **独特视角**：从"格式暴政"到"信用复利"
5. **行动建议**：4条可落地的建议

## 参考来源

- 卓克《科学人物课：冯·诺伊曼》
- 卓克《科技参考：学术期刊演化史》

---

*生成时间：2026-03-18*
