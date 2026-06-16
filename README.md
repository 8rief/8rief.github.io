# 8rief Notes

个人技术笔记站，记录安全查询、隐私计算和相关开源系统的源码阅读与构造复盘。文章以单个问题为单位，尽量从背景、定义、分析到结论逐步展开。

A personal technical notebook for secure query systems, privacy-preserving computation, and source-code-oriented retrospectives. Each post focuses on one concrete question and follows a background-definition-analysis-takeaway structure when applicable.

## 内容范围 / Scope

- 安全查询系统源码阅读 / Source reading for secure query systems
- PIR、DPF、FSS、PCG 等密码工具学习笔记 / Notes on PIR, DPF, FSS, PCG, and related tools
- 构造尝试失败原因与边界条件复盘 / Retrospectives on failed constructions and boundary conditions
- 可公开的实验现象、计算结论和后续问题 / Publicly shareable measurements, calculations, and open questions

## 写作方式 / Style

- 一篇文章只讨论一个具体问题。
- 技术细节尽量对照论文、公开源码和可复查的实测或计算结果。
- 不发布未公开方案的完整协议细节、私有 raw data、账号密钥或本地路径。

Each post is scoped to one question. Technical claims should be grounded in papers, public code, or reproducible measurements/calculations. Unpublished protocol details, private raw data, credentials, and local paths are excluded.

## 本地编辑 / Local editing

正式文章放在 `_posts/`：

```text
_posts/YYYY-MM-DD-short-title.md
```

常用命令：

```bash
git status
git add _posts README.md
git commit -m "Update notes"
git push
```

GitHub Pages will rebuild the site after each push to `main`.
