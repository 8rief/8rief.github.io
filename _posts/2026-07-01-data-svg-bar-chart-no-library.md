---
layout: post
title: "不用绘图库也能画图：从 summary 生成 SVG 柱状图"
date: 2026-07-01 11:35:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用地区收入数据解释坐标、比例、标签和图表边界。"
tags: [svg, data-visualization, chart, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / SVG / bar chart / no library
> 本文 lab 已验证：`reports/region_revenue.svg` 生成成功，并包含 East 地区收入柱。

可视化的核心是把数据映射成视觉编码。柱状图的最小模型很简单：数值决定高度，类别决定横向位置，标签解释含义。先用 SVG 手写一次，后续使用 matplotlib、ECharts 或 Vega-Lite 时更容易理解它们在帮你做什么。

## 学习目标

1. 理解柱状图的类别轴和值轴。
2. 用 summary 中的地区收入生成 SVG。
3. 知道图表必须写清单位、数据来源和边界。

## 先修知识

知道 `summary.json` 中已经有 `by_region` 数组。

## 核心模型

![SVG 柱状图生成模型](/assets/diagrams/data-svg-bar-chart-no-library.svg)

每个地区对应一个矩形。收入越高，矩形越高。坐标计算和标签生成都来自同一份 `by_region` 数据。

## 可信资料的关键结论

- MDN SVG 文档说明 SVG 是用于构造、绘制和布局矢量图形的 Web 技术。
- SVG 是文本格式，适合版本控制和自动生成。
- 柱状图适合比较少量类别的绝对值；本包的地区收入正好符合这个场景。

## 逐步实现

取最大值：

```python
max_value = max(float(item["revenue"]) for item in by_region)
```

计算高度：

```python
h = revenue / max_value * chart_height
y = chart_top + chart_height - h
```

生成矩形：

```python
parts.append(
    f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{h:.1f}" rx="8"/>'
)
```

输出图表：

```text
reports/region_revenue.svg
```

这张图使用 zero-baseline 纵轴，从 0 开始比较地区收入，避免夸大差异。

## 常见错误

1. **只画图，不写单位。** 读者不知道数值代表什么。
2. **比例从非零起点开始。** 小差异会被放大。
3. **图表直接读原始数据。** 应从清洗和汇总结果生成。
4. **图片不可复查。** SVG 是文本，可以被版本控制和 XML 解析检查。

## 练习或延伸

1. 把图表改成按月份收入绘制。
2. 给最高柱增加不同颜色。
3. 把 `by_region` 改成按原始地区顺序输出，观察图表顺序变化。

## 参考资料

- MDN：[SVG](https://developer.mozilla.org/en-US/docs/Web/SVG)
- MDN：[SVG element reference](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/svg)

{% endraw %}
