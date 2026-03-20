# WeChat Publish / Content Discovery Bot

一个可落地的 **微信公众号草稿发布系统**，同时保留内容采集与文章生成能力。  
当前仓库最核心、最稳定、最适合直接使用的部分，是这套发布链路：

- 单篇文章配置化发布
- HTML 正文图片自动上传替换
- 批量队列发布
- `schedule` 定时发布逻辑
- 发布日志总表

---

## 10 秒看懂这个仓库

如果你只关心“怎么发公众号草稿”，只需要记住两条命令：

### 单篇发布

```bash
python publish_to_wechat.py --config drafts/queue/your-article/meta.json --auto
```

### 批量发布队列中 ready / 到时 scheduled 的文章

```bash
python publish_ready_queue.py
```

---

## 最短上手路径

### 第 1 步：准备一篇文章目录

```text
drafts/
  queue/
    2026-03-25-single-agent-value/
      article.html
      cover.jpg
      meta.json
      illustration_1.jpg
      illustration_2.jpg
```

### 第 2 步：写 `meta.json`

#### 立即可发

```json
{
  "title": "文章标题",
  "author": "深蓝",
  "digest": "文章摘要",
  "html": "article.html",
  "cover": "cover.jpg",
  "schedule": "2026-03-25 09:00",
  "status": "ready"
}
```

#### 定时进入发布队列

```json
{
  "title": "文章标题",
  "author": "深蓝",
  "digest": "文章摘要",
  "html": "article.html",
  "cover": "cover.jpg",
  "schedule": "2026-03-25 09:00",
  "status": "scheduled"
}
```

### 第 3 步：执行发布

#### 发单篇

```bash
python publish_to_wechat.py --config drafts/queue/2026-03-25-single-agent-value/meta.json --auto
```

#### 扫描整个队列

```bash
python publish_ready_queue.py
```

---

## 这套系统会自动帮你做什么

你不需要手工上传正文图片。

系统会自动：

1. 读取 `article.html`
2. 扫描所有 `<img src="...">`
3. 跳过远程 URL 和 `data:` 图片
4. 上传本地图片到公众号
5. 替换 HTML 中图片地址为公众号 URL
6. 推送到公众号草稿箱
7. 写入发布日志

---

## 典型工作流

```text
准备文章目录
   ↓
填写 meta.json
   ↓
设置 status=ready 或 scheduled
   ↓
运行单篇发布 / 批量发布器
   ↓
公众号草稿箱生成草稿
   ↓
记录 media_id / published_at / 发布日志
```

---

## 仓库当前重点文件

```text
content-discovery-bot/
├── publish_to_wechat.py           # 单篇公众号发布脚本
├── publish_ready_queue.py         # 批量队列发布器
├── BATCH_PUBLISH_MANUAL.md        # 完整使用手册
├── WECHAT_PUBLISH_WORKFLOW.md     # 发布工作流说明
├── publish_log.jsonl              # 结构化发布日志
├── publish_log.csv                # 表格发布日志
├── drafts/
│   ├── README_BATCH_PUBLISH.md    # 队列目录说明
│   └── queue/
│       ├── _template/             # 模板目录
│       └── 2026-03-20-five-dynasties/
└── src/                           # 原有内容采集 / 分析 / 生成代码
```

---

## 发布日志

系统会自动生成两类日志：

### `publish_log.jsonl`
- 一行一条记录
- 适合程序读取

### `publish_log.csv`
- 可直接用 Excel 打开
- 适合人工查看发布历史

记录字段包括：

- `logged_at`
- `mode`
- `status`
- `title`
- `author`
- `digest`
- `html`
- `cover`
- `config_path`
- `media_id`
- `error`

---

## 推荐阅读顺序

如果你要真正接手这套系统，建议按下面顺序看：

1. `BATCH_PUBLISH_MANUAL.md`
2. `drafts/README_BATCH_PUBLISH.md`
3. `publish_to_wechat.py`
4. `publish_ready_queue.py`

---

## 当前适用场景

这套仓库现在最适合：

- 单篇公众号文章推草稿
- 多篇内容批量排队入草稿箱
- 按 `schedule` 做定时发布
- 做系列化内容生产
- 对发布历史做留痕和回查

---

## 仓库里的另一层能力

仓库仍保留原有内容采集 / 分析 / 文章生成能力，包括：

- 多源选题采集
- LLM 分析与生成
- 草稿生产
- 配图生成

但如果你是第一次进入这个仓库，建议优先使用已经跑通的 **微信发布链路**。

---

## 后续可继续扩展

如果继续往前做，优先级建议是：

1. 接入 Windows 定时任务 / cron
2. 增加标题 / 摘要校验器
3. 增加多账号配置层
4. 增加统一发布历史面板

---

## 相关文档

- `BATCH_PUBLISH_MANUAL.md`
- `WECHAT_PUBLISH_WORKFLOW.md`
- `drafts/README_BATCH_PUBLISH.md`
- `RELEASE_README.md`

---

## 作者

深蓝 · 深蓝的会客厅
