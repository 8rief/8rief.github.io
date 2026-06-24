# 8rief Notes

个人技术笔记站，按四条主线组织：项目展示、问题探究、计算机技术教学、算法与数据结构。

A personal technical notebook organized around project showcases, problem explorations, computer science teaching notes, and algorithms/data-structures notes.

## 栏目 / Columns

- `project-showcase` / 项目展示：已经有 demo、报告、静态页或可复现接口的项目。文章必须讲清痛点、设计目标、详细设计、技术实现、复现方式和边界。
- `problem-exploration` / 问题探究：研究问题、源码阅读、负结果、实验现象和边界推理。文章必须讲清问题、关键难点、分析路径、证据边界、结论和下一步。
- `computer-science-teaching` / 计算机技术教学：教学型计算机技术文章。文章必须讲清学习目标、先修知识、核心模型、逐步实现、常见错误和练习。
- `algorithms-data-structures` / 算法与数据结构：算法和数据结构专题。文章必须讲清问题模型、不变量、正确性理由、复杂度、C++ 实现、测试边界和练习。

Existing post URLs are preserved by keeping the original `categories`; the stable site columns are stored in each post's `column` front matter.

## 常用命令

```bash
git status
git add _posts README.md *.md _config.yml assets/diagrams
git commit -m "Update notes"
git push
```

GitHub Pages rebuilds the site after each push to `main`.
