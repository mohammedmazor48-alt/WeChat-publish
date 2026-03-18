# Content Discovery Bot

社媒爆款选题采集与公众号文章生成系统

## 功能特性

- 🔍 **多源采集**: Reddit、Hacker News、RSS订阅
- 🧠 **AI分析**: LLM评估选题价值，智能评分
- ✍️ **文章生成**: 轻量/深度双模式，支持风格DNA
- 🔄 **自动调度**: 定时运行，无需人工干预
- 🖥️ **Web界面**: Streamlit可视化操作台
- 📊 **数据分析**: 运行日志和统计报告

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <your-repo>
cd content-discovery-bot

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入API密钥
```

`.env` 文件示例:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 3. 初始化系统

```bash
# 初始化数据库和目录
content-bot init
```

### 4. 运行工作流

```bash
# 手动运行一次
content-bot run

# 或启动定时调度
content-bot schedule start
```

### 5. 启动Web界面

```bash
streamlit run src/content_discovery_bot/app.py
```

## CLI命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 初始化数据库和目录 | `content-bot init` |
| `run` | 运行工作流 | `content-bot run --mode full` |
| `schedule` | 管理定时调度 | `content-bot schedule start` |
| `drafts` | 查看草稿 | `content-bot drafts --status pending` |
| `review` | 审核草稿 | `content-bot review 123 approve` |
| `report` | 生成报告 | `content-bot report --days 7` |
| `generate` | 手动生成文章 | `content-bot generate "主题" --mode deep` |

## 工作流说明

### 数据采集流程
1. **采集**: 从各平台获取最新内容
2. **去重**: SimHash算法去重
3. **分析**: LLM评估选题价值（热度、深度、争议性等）
4. **排序**: 多维度加权评分，选出Top选题
5. **生成**: 根据选题自动或手动生成文章

### 生成模式

**轻量模式** (lightweight)
- 适合常规选题
- 模板填充 + LLM润色
- 成本低，速度快

**深度模式** (deep)
- 适合重要选题
- LLM原生生成
- 质量高，成本较高

## 项目结构

```
content-discovery-bot/
├── config.yaml              # 配置文件
├── .env                     # 环境变量
├── requirements.txt         # 依赖列表
├── pyproject.toml          # 项目元数据
├── references/
│   └── style-dna.md        # 写作风格DNA
├── src/
│   └── content_discovery_bot/
│       ├── __init__.py
│       ├── config.py        # 配置加载
│       ├── models.py        # 数据模型
│       ├── database.py      # 数据库操作
│       ├── collector.py     # 内容采集
│       ├── analyzer.py      # 选题分析
│       ├── generator.py     # 文章生成
│       ├── workflow.py      # 工作流管道
│       ├── cli.py           # 命令行界面
│       └── app.py           # Web界面
└── data/                    # 数据目录
    ├── content_discovery.db # SQLite数据库
    └── drafts/              # 文章草稿
```

## 配置说明

### 数据源配置

编辑 `config.yaml`:

```yaml
sources:
  hackernews:
    enabled: true
    min_score: 100
    check_interval_hours: 6
  
  rss:
    enabled: true
    feeds:
      - name: "即刻精选"
        url: "https://rsshub.app/jike/topic/selected"
        category: "社交热点"
        check_interval_hours: 4
```

### 分析器配置

```yaml
analyzer:
  min_total_score: 25        # 通过阈值
  deep_mode_threshold: 35    # 深度模式阈值
  simhash_threshold: 3       # 去重阈值
```

### LLM配置

```yaml
llm:
  provider: "openai"         # 或 "anthropic"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
  max_tokens: 4000
  temperature: 0.7
```

## 开发计划

### Phase 1: MVP (已完成)
- [x] 基础架构搭建
- [x] HN + RSS采集
- [x] LLM选题分析
- [x] 文章生成功能
- [x] CLI界面
- [x] Web界面

### Phase 2: 优化 (待实现)
- [ ] Reddit集成
- [ ] 评分模型训练
- [ ] 反馈闭环
- [ ] 自动化发布
- [ ] 监控告警

### Phase 3: 扩展 (未来)
- [ ] 多账号支持
- [ ] 机器学习模型
- [ ] 多语言支持
- [ ] 分布式部署

## 注意事项

1. **API成本**: LLM调用会产生费用，建议设置预算上限
2. **合规性**: 仅使用官方API或公开RSS，遵守平台规则
3. **内容版权**: 生成文章为原创内容，参考内容仅作选题参考

## License

MIT License

## 作者

深蓝 - 深蓝的会客厅
