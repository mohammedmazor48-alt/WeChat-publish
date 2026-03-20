# Article Template

把一篇待发布文章放进这个目录结构：

- `article.html`：正文 HTML
- `cover.jpg`：封面图
- `meta.json`：文章配置
- 其他图片：正文中引用的任意本地图片

注意：`article.html` 中如果要展示封面图，图片引用也请统一写成 `cover.jpg`，这样目录内资源命名保持一致。

建议复制本目录为新文章目录，例如：

```bash
xcopy /E /I D:\tools\content-discovery-bot\drafts\queue\_template D:\tools\content-discovery-bot\drafts\queue\2026-03-25-single-agent-value
```

然后替换里面的内容即可。
