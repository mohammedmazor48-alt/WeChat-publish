# 微信公众号批量定期发文使用手册

## 一、这套系统现在能做什么

当前发布系统已经支持：

1. 单篇文章按配置文件推送到公众号草稿箱
2. 自动上传封面图
3. 自动扫描 HTML 中的正文本地图片并上传
4. 自动替换 HTML 中图片路径为公众号可用 URL
5. 批量扫描 `drafts/queue/` 队列
6. 支持两种发布状态：
   - `ready`：立即可发
   - `scheduled`：到达计划时间后可发
7. 发布成功后自动回写：
   - `status`
   - `last_media_id`
   - `published_at`
8. 自动记录发布日志总表：
   - `publish_log.jsonl`
   - `publish_log.csv`

---

## 二、目录结构规范

每篇文章一个目录，放在：

```text
D:\tools\content-discovery-bot\drafts\queue\
```

示例：

```text
drafts\queue\2026-03-25-single-agent-value\
  article.html
  cover.jpg
  meta.json
  illustration_1.jpg
  illustration_2.jpg
```

### 文件说明

- `article.html`：公众号正文 HTML
- `cover.jpg`：封面图
- `meta.json`：文章配置文件
- 其他图片：正文中引用的任意本地图片

**注意：**
如果 `article.html` 中也展示封面图，请统一写成：

```html
<img src="cover.jpg">
```

这样目录内资源才一致。

---

## 三、meta.json 写法

### 1）立即可发（ready）

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

### 2）定时发布（scheduled）

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

### 字段说明

- `title`：公众号标题
- `author`：作者名
- `digest`：摘要
- `html`：正文 HTML 文件名（相对当前目录）
- `cover`：封面图文件名（相对当前目录）
- `schedule`：计划发布时间
- `status`：文章状态

### `schedule` 支持格式

- `2026-03-25 09:00`
- `2026-03-25 09:00:00`

---

## 四、文章图片怎么处理

你不需要手工上传正文图。

系统会自动：

1. 读取 `article.html`
2. 找出所有 `<img src="...">`
3. 跳过远程 URL 和 `data:` 图片
4. 上传本地图片到公众号
5. 将 HTML 中图片地址替换成公众号 URL

### 推荐写法

```html
<img src="illustration_1.jpg">
<img src="charts/data-1.png">
<img src="cover.jpg">
```

只要图片文件实际存在，就能自动处理。

---

## 五、日常使用流程

### 方案 A：发布单篇文章

适合手动推某一篇。

命令：

```bash
python publish_to_wechat.py --config drafts/queue/2026-03-20-five-dynasties/meta.json --auto
```

### 方案 B：批量发布队列文章

适合统一扫队列。

命令：

```bash
python publish_ready_queue.py
```

脚本会自动：

- 发布 `status=ready` 的文章
- 发布 `status=scheduled` 且已到时间的文章
- 跳过未来时间的 `scheduled`
- 跳过已 `published` 的文章

---

## 六、发布后的状态变化

### 发布成功后，系统会自动回写：

```json
{
  "status": "published",
  "last_media_id": "xxxxx",
  "published_at": "2026-03-20 12:05:56"
}
```

### 发布失败时，会写入：

```json
{
  "last_error_at": "2026-03-20 12:08:00"
}
```

这样方便回查。

---

## 七、推荐的运营动作

### 1）新建文章

最简单的方式：复制模板目录

```text
drafts\queue\_template
```

复制为：

```text
drafts\queue\2026-03-25-single-agent-value
```

然后替换：
- `article.html`
- `cover.jpg`
- 正文配图
- `meta.json`

### 2）准备发布

如果准备立即进队列：

```json
"status": "ready"
```

如果准备定时发布：

```json
"status": "scheduled"
```

并设置好：

```json
"schedule": "2026-03-25 09:00"
```

### 3）执行批量发布

```bash
python publish_ready_queue.py
```

### 4）去公众号后台确认草稿

登录：

<https://mp.weixin.qq.com>

进入：
- 内容管理
- 草稿箱

检查：
- 标题
- 封面
- 摘要
- 正文图片
- 排版

---

## 八、常见问题

### Q1：正文图为什么没进去？
先检查：
- HTML 里是否真的有 `<img src="...">`
- 图片文件是否存在
- 路径是否相对 `article.html` 可解析

### Q2：为什么文章没被批量发布器扫到？
检查：
- `meta.json` 是否存在
- `status` 是否是 `ready` 或 `scheduled`
- 如果是 `scheduled`，当前时间是否已到 `schedule`

### Q3：为什么已经发布过的文章不会重复发？
因为成功后系统会自动把：

```json
"status": "published"
```

批量发布器只会扫：
- `ready`
- 已到时间的 `scheduled`

### Q4：如果我想重发怎么办？
手动把 `status` 改回：

```json
"status": "ready"
```

然后重新执行批量发布器或单篇发布命令。

---

## 九、发布日志总表

系统现在会自动生成两份日志：

### 1）结构化日志

- `D:\tools\content-discovery-bot\publish_log.jsonl`

特点：
- 一行一条记录
- 适合程序读取
- 保留完整字段

### 2）表格日志

- `D:\tools\content-discovery-bot\publish_log.csv`

特点：
- 可以直接用 Excel 打开
- 适合人工查看
- 方便统计已发布文章

### 日志字段

- `logged_at`
- `mode`（single / queue）
- `status`（success / failed）
- `title`
- `author`
- `digest`
- `html`
- `cover`
- `config_path`
- `media_id`
- `error`

---

## 十、推荐命令速查

### 单篇发布

```bash
python publish_to_wechat.py --config drafts/queue/某篇文章/meta.json --auto
```

### 批量发布

```bash
python publish_ready_queue.py
```

---

## 十一、当前结论

这套系统已经适合：

- 单篇发文
- 多篇排队
- 定时发文
- 批量推草稿
- 草稿状态留痕

后续如果再升级，优先建议：

1. 接系统定时任务（真正自动化）
2. 增加发布日志总表
3. 增加摘要/标题自动校验
