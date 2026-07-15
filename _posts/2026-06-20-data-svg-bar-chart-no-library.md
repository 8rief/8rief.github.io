---
layout: post
title: "不用绘图库也能画图：从 summary 生成 SVG 柱状图"
date: 2026-06-20 09:00:00 +0800
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

## 为什么需要手写一次 SVG

绘图库能快速出图，但初学者容易只会调参数，不理解图表从数据到像素的映射。手写一次 SVG 可以把柱状图的关键机制摊开：最大值如何决定比例，数值如何换成高度，标签如何绑定到类别，坐标系为什么需要从底部向上计算。

这个练习的目标是建立可视化的底层心智模型；matplotlib 或 ECharts 适合在后续项目里承担更复杂的布局和交互。理解了这些变量后，使用任何绘图库时都能判断图是否表达了正确问题。

本图的设计选择很少：

1. 横轴是地区类别。
2. 纵轴从 0 开始表示收入。
3. 柱高按 `revenue / max_value` 缩放。
4. 标签直接写出两位小数，避免只靠视觉估计。

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

## 输出怎么读

当前图表使用 `by_region` 的四个值：

```text
East  202.25
South 197.25
West  171.50
North 165.30
```

最大值是 East 的 202.25，所以 East 的柱子占满可用图表高度。North 的高度大约是 `165.30 / 202.25 = 0.817` 倍。因为纵轴从 0 起，读者看到的是绝对收入差异，不会被截断坐标夸大。

SVG 文件中每个柱子是一个 `<rect>`，每个标签是一个 `<text>`。这也是它适合审计的原因：即使不打开浏览器，也可以用文本搜索确认标题、地区名和数值是否存在。

## 什么时候该用绘图库

手写 SVG 适合教学和少量固定图表。真实项目中，如果需要坐标轴刻度自动布局、交互图例、多系列图、颜色主题或导出多格式图像，就应使用成熟绘图库。无论换成什么工具，仍要保持同一条原则：图表从 `summary.json` 读取已经确认的指标。

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
