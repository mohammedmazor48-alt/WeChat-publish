# Batch Publish Structure

## 推荐目录结构

```text
D:\tools\content-discovery-bot\drafts\
  queue\
    2026-03-20-five-dynasties\
      article.html
      cover.jpg
      meta.json
      illustration_1.jpg
      illustration_2.jpg
      illustration_3.jpg
      illustration_4.jpg
    2026-03-22-credit-rebuild\
      article.html
      cover.jpg
      meta.json
      illustration_1.jpg
```

每篇文章一个独立文件夹，里面放：
- `article.html`：正文 HTML
- `cover.jpg`：封面图
- `meta.json`：文章元数据
- 其他正文配图：任意文件名都可以，只要 HTML 里正确引用

---

## meta.json 模板

```json
{
  "title": "文章标题",
  "author": "深蓝",
  "digest": "文章摘要",
  "html": "article.html",
  "cover": "cover.jpg",
  "schedule": "2026-03-22 09:00",
  "status": "draft"
}
```

字段说明：
- `title`：公众号标题
- `author`：作者名
- `digest`：摘要
- `html`：HTML 文件名（相对当前目录）
- `cover`：封面图文件名（相对当前目录）
- `schedule`：计划发布时间，先作为运营字段保留
- `status`：内容状态，建议用 `draft` / `ready` / `published`

---

## 当前使用方式

进入具体文章目录后，可按下面方式调用：

```bash
cd D:\tools\content-discovery-bot
python publish_to_wechat.py \
  --title "文章标题" \
  --html drafts\queue\2026-03-20-five-dynasties\article.html \
  --cover drafts\queue\2026-03-20-five-dynasties\cover.jpg \
  --author "深蓝" \
  --digest "文章摘要" \
  --auto
```

---

## 建议的运营流程

1. 新建一篇文章目录
2. 放入 `article.html`、`cover.jpg`、配图
3. 填写 `meta.json`
4. 内容确认后推到公众号草稿箱
5. 推送完成后把 `status` 改为 `published` 或归档

---

## 命名建议

目录名建议：

```text
YYYY-MM-DD-topic-slug
```

例如：
- `2026-03-20-five-dynasties`
- `2026-03-22-credit-rebuild`
- `2026-03-25-single-agent-value`

这样方便排序、检索、批量管理。
