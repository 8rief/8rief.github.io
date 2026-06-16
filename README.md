# Brief 的研究笔记

这是一个 GitHub Pages 个人博客仓库，主要记录安全查询、隐私计算、源码阅读、失败构造复盘和未来研究问题。

## 修改文章

正式发布的文章放在：

```text
_posts/YYYY-MM-DD-title.md
```

每篇文章开头必须有 front matter，例如：

```yaml
---
layout: post
title: "文章标题"
date: 2026-06-16 10:00:00 +0800
categories: secure-query
tags: [waldo, fss, source-reading]
---
```

修改文章后提交：

```bash
git add .
git commit -m "Update blog post"
git push
```

GitHub Pages 会自动更新站点。

## 写作边界

- 一篇文章只聚焦一个问题。
- 写源码阅读、学习笔记、失败路径复盘和未来问题地图。
- 不发布未公开方案细节、专利敏感内容、私有 raw data、账号密钥或个人本地路径。
