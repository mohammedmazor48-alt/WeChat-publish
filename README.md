# WeChat Publish / Content Discovery Bot

一个面向微信公众号内容生产的工作流仓库：
既能做**选题采集与文章生成**，也已经具备一套可落地的 **公众号草稿发布系统**。

当前这套仓库最实用的部分，是已经跑通了：

- 单篇文章配置化发布
- HTML 正文图片自动上传替换
- 批量队列发布
- `schedule` 定时发布逻辑
- 发布日志总表

---

## 仓库当前重点能力

### 1. 微信公众号发布系统

已支持：

- 封面图上传
- 自动扫描 HTML 中的本地图片并上传到公众号
- 自动将图片路径替换成公众号 URL
- 推送文章到公众号草稿箱
- 单篇 `--config` 发布
- 队列批量发布
- `ready / scheduled / published` 状态流转
- 生成发布日志（JSONL + CSV）

### 2. 内容采集与文章生成

仓库仍保留原有内容采集/分析能力，包括：

- 多源选题采集
- LLM 分析与生成
- 草稿生产
- 配图生成

但如果你是第一次进入这个仓库，建议优先看发布链路，而不是旧的采集能力说明。

---

## 推荐阅读顺序

如果你是来使用这套系统，建议按下面顺序看：

1. `BATCH_PUBLISH_MANUAL.md`  
   批量定期发文使用手册
2. `drafts/README_BATCH_PUBLISH.md`  
   队列目录结构说明
3. `publish_to_wechat.py`  
   单篇配置化发布脚本
4. `publish_ready_queue.py`  
   批量 / 定时队列发布脚本

---

## 快速开始

### 1）安装依赖

```bash
cd content-discovery-bot
pip install -r requirements.txt
```

### 2）配置环境变量

确保 `.env` 中有公众号配置。

### 3）准备一篇文章目录

推荐目录结构：

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

### 4）单篇发布

```bash
python publish_to_wechat.py --config drafts/queue/2026-03-25-single-agent-value/meta.json --auto
```

### 5）批量发布 ready / scheduled 文章

```bash
python publish_ready_queue.py
```

---

## 目录结构（当前重点）

```text
content-discovery-bot/
├── publish_to_wechat.py           # 单篇公众号发布脚本
├── publish_ready_queue.py         # 批量队列发布器
├── BATCH_PUBLISH_MANUAL.md        # 使用手册
├── WECHAT_PUBLISH_WORKFLOW.md     # 发布工作流说明
├── publish_log.jsonl              # 结构化发布日志
├── publish_log.csv                # 表格发布日志
├── drafts/
│   ├── README_BATCH_PUBLISH.md    # 队列目录说明
│   └── queue/
│       ├── _template/             # 模板目录
│       └── 2026-03-20-five-dynasties/
│           ├── article.html
│           ├── cover.jpg
│           ├── meta.json
│           └── illustration_*.jpg
├── src/                           # 原有内容采集/生成代码
├── data/                          # 数据文件
└── references/                    # 参考资料
```

---

## `meta.json` 示例

### ready（立即可发）

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

### scheduled（定时进入发布队列）

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

---

## 日志文件

系统现在会自动写两类日志：

### `publish_log.jsonl`
- 一行一条发布记录
- 适合程序处理

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

## 当前适用场景

这套仓库目前最适合：

- 单篇公众号文章推草稿
- 多篇内容排队入草稿箱
- 按 `schedule` 定时进入发布流程
- 对发布历史做留痕和回查
- 做系列化内容生产

---

## 下一步可扩展方向

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
