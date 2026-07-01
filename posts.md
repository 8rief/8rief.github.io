---
layout: page
title: Posts
permalink: /posts/
---

## 项目展示

{% assign project_posts = site.posts | where: "column", "project-showcase" %}
{% for post in project_posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}

## 问题探究

{% assign problem_posts = site.posts | where: "column", "problem-exploration" %}
{% for post in problem_posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}

## 计算机技术教学

{% assign teaching_posts = site.posts | where: "column", "computer-science-teaching" %}
{% if teaching_posts.size == 0 %}
暂无文章。
{% else %}
{% for post in teaching_posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}

## 算法与数据结构

{% assign algorithm_posts = site.posts | where: "column", "algorithms-data-structures" %}
{% if algorithm_posts.size == 0 %}
暂无文章。
{% else %}
{% for post in algorithm_posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}

## 数学基础

{% assign math_posts = site.posts | where: "column", "mathematical-foundations" %}
{% if math_posts.size == 0 %}
暂无文章。
{% else %}
{% for post in math_posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
