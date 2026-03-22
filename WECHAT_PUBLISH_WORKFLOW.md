# WeChat Publish Workflow

## 当前已实现能力

`publish_to_wechat.py` 现在已经支持：

1. 获取微信公众号 `access_token`
2. 上传封面图（永久素材，返回 `thumb_media_id`）
3. 自动上传正文插图（返回可直接用于 HTML 的图片 URL）
4. 自动替换 HTML 中的本地图片路径
5. 推送草稿到公众号后台
6. 支持 `--auto` 自动执行

---

## 标准文件约定

建议每篇文章都按下面结构准备：

### 文章文件
- HTML 正文：`drafts/article_xxx.html`
- 封面图：`drafts/cover_xxx.jpg`
- 正文插图：
  - `drafts/illustration_1.jpg`
  - `drafts/illustration_2.jpg`
  - `drafts/illustration_3.jpg`
  - ...

### HTML 图片引用写法
正文中直接写：

```html
<img src="illustration_1.jpg" alt="示意图1">
<img src="illustration_2.jpg" alt="示意图2">
```

脚本会自动上传这些图片并替换成公众号图片 URL。

---

## 推送流程

```bash
cd D:\tools\content-discovery-bot
python publish_to_wechat.py --auto
```

---

## 当前脚本默认使用的文件

- 封面：`drafts/cover_five_dynasties.jpg`
- 正文：`drafts/article_five_dynasties.html`

如果以后要复用，建议把脚本进一步改成支持命令行参数，例如：

```bash
python publish_to_wechat.py \
  --title "标题" \
  --html drafts/article_xxx.html \
  --cover drafts/cover_xxx.jpg \
  --author "深蓝" \
  --digest "摘要"
```

---

## 后续建议优化

下一步最值得做的两件事：

1. **参数化脚本**
   - 支持 `--title`
   - 支持 `--html`
   - 支持 `--cover`
   - 支持 `--digest`
   - 支持 `--author`

2. **自动扫描当前文章配图**
   - 不只是扫描 `illustration_1.jpg` 到 `illustration_9.jpg`
   - 而是从 HTML 中提取 `<img src>` 自动上传

---

## 当前结论

现在这套流程已经能稳定完成：

**封面图 + 正文插图 + HTML 替换 + 草稿推送**

适合后续持续复用。
