---
layout: post
title: "CNN 第一课：卷积、padding、stride 和 pooling 为什么能识别平移后的形状"
date: 2026-04-12 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, cnn, convolution, pooling, baseline, teaching]
---

前面已经用 majority baseline、线性 baseline 和 NumPy MLP 跑过分类实验。下一步进入图像类任务时，最容易混淆的问题是：如果一个形状从左边移动到右边，模型到底应该重新记住一套像素位置，还是应该识别“同一个局部形状出现在了新位置”？

这篇只解决第一层机制问题：卷积核怎样在整张图上复用同一组权重，padding 和 stride 怎样改变扫描范围，ReLU 和 pooling 怎样把局部响应变成更稳定的特征。配套实验不用 NumPy/PyTorch，只用 Python list，把每一步写到可以检查的程度。

配套代码在 [`deep-learning-cnn-foundations`](/labs/#deep-learning-cnn-foundations)，也可以直接看 [`README.md`](/assets/labs/deep-learning-cnn-foundations/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-cnn-foundations/run_lab.sh)。

## 先看要解决的失败

假设图片是一个 8x8 网格，类别只有两种：竖线和横线。训练集中，竖线只出现在第 1、2 列，横线只出现在第 1、2 行；测试集中，同样的竖线和横线移动到第 5、6 列/行。

这个设置很小，但它抓住了图像模型的一个真实痛点：如果分类器只记住训练像素出现过的位置，它会把“形状移动了”误判成“类别变了”。

本实验比较三种方法：

| 方法 | 看到什么 | 预期问题 |
| --- | --- | --- |
| majority baseline | 只输出训练集中最多的类别 | 类别平衡时只能做到 50% |
| raw position-template baseline | 把 8x8 像素展平成 64 维，再和每类训练模板比较距离 | 位置绑定太强，测试形状一平移就失效 |
| convolution + global max feature | 用同一组方向滤波器扫描所有位置，再取最强响应 | 能在这个 toy setting 里识别平移后的同一形状 |

这里必须保留 baseline。没有 baseline，就无法判断 CNN 的机制到底解决了哪个具体失败。

## 实验怎么跑

在公开仓库中执行：

```bash
cd assets/labs/deep-learning-cnn-foundations
bash run_lab.sh
```

成功时会看到这些稳定标记：

```text
TRAIN_SAMPLES=4
TEST_SAMPLES=4
MAJORITY_BASELINE_ACC=0.500
RAW_TEMPLATE_ACC=0.000
CONV_FEATURE_ACC=1.000
SHIFT_GENERALIZATION_GAIN=1.000
VERTICAL_FILTER_RESPONSE_OK=yes
HORIZONTAL_FILTER_RESPONSE_OK=yes
RUN_STATUS=ok
deep_learning_cnn_lab_status=ok
```

运行后本地会生成：

- `reports/cnn_probe.json`：机器可读的样本数、accuracy、逐样本响应。
- `reports/cnn_report.md`：人能读的对比表。
- `reports/feature_table.csv`：每个测试样本的原始模板预测、卷积预测、方向响应。

公开仓库不提交 `reports/`。这些输出应由学习者在自己的机器上重新生成。

## 卷积核在做什么

先写一个最小的竖线检测核：

```python
VERTICAL_KERNEL = [
    [-1.0, 2.0, -1.0],
    [-1.0, 2.0, -1.0],
    [-1.0, 2.0, -1.0],
]
```

这个 3x3 窗口的中间列是正权重，两边是负权重。当窗口中心压在一条竖线上时，中间列的亮像素贡献正分；如果窗口里只是背景，或者亮像素更像横线，响应就不会高。

横线检测核换成中间行加正权重：

```python
HORIZONTAL_KERNEL = [
    [-1.0, -1.0, -1.0],
    [2.0, 2.0, 2.0],
    [-1.0, -1.0, -1.0],
]
```

卷积计算本身就是窗口乘加。实验代码里的核心循环是：

```python
def conv2d(image, kernel, *, padding=0, stride=1):
    source = pad2d(image, padding)
    out_h = (len(source) - len(kernel)) // stride + 1
    out_w = (len(source[0]) - len(kernel[0])) // stride + 1
    out = zeros(out_h, out_w)
    for out_r in range(out_h):
        for out_c in range(out_w):
            acc = 0.0
            base_r = out_r * stride
            base_c = out_c * stride
            for kr in range(len(kernel)):
                for kc in range(len(kernel[0])):
                    acc += source[base_r + kr][base_c + kc] * kernel[kr][kc]
            out[out_r][out_c] = acc
    return out
```

注意这里的关键在于同一个 `kernel` 会被放到所有 `(base_r, base_c)` 位置。这个“权重共享”让竖线检测器可以在左边检测竖线，也可以在右边检测竖线。

## padding、stride、ReLU、pooling 各自解决什么

CNN 第一课常见的误区是把这些词一起背下来。更好的读法是从需求出发。

| 组件 | 直接需求 | 在实验中的作用 |
| --- | --- | --- |
| padding | 边缘也要被窗口覆盖，输出尺寸不要过快变小 | `padding=1` 让 3x3 核扫描 8x8 图时仍保留边缘响应机会 |
| stride | 不一定每移动 1 个像素都算一次；需要控制采样密度和输出大小 | 本实验卷积 `stride=1`，pooling `stride=2` |
| ReLU | 只保留“这个特征出现了”的正响应，压掉负响应 | 方向核负分不再干扰后面的最大值 |
| max pooling | 在局部区域内保留最强响应，降低对精确位置的敏感性 | 2x2 pooling 后，同一条线小幅移动仍能留下强信号 |
| global max | 对这个 toy classifier，只关心整张图里某个方向特征是否出现 | 取竖线响应最大值、横线响应最大值，然后比较 |

实验里的特征提取函数就是这条链路：

```python
def conv_features(image):
    vertical_map = max_pool2d(relu(conv2d(image, VERTICAL_KERNEL, padding=1)), size=2, stride=2)
    horizontal_map = max_pool2d(relu(conv2d(image, HORIZONTAL_KERNEL, padding=1)), size=2, stride=2)
    return {
        "vertical_response": global_max(vertical_map),
        "horizontal_response": global_max(horizontal_map),
    }
```

真实 CNN 会学习卷积核参数，会有多通道、多层、loss、optimizer 和反向传播。本实验把卷积核手写出来，是为了先把机制看清楚：同一组局部检测器扫过所有位置，然后把响应汇总成分类特征。

数据流可以先画成这样：

```text
8x8 image
   │
   ├─ pad=1 ─ conv with vertical kernel ─ ReLU ─ 2x2 max pool ─ global max ─ vertical_response
   │
   └─ pad=1 ─ conv with horizontal kernel ─ ReLU ─ 2x2 max pool ─ global max ─ horizontal_response

prediction = vertical if vertical_response >= horizontal_response else horizontal
```

## 为什么 raw template 会输得这么彻底

raw position-template baseline 把图片展平成 64 个像素，然后为每个类别算一个训练中心。竖线训练中心只在第 1、2 列有强信号；横线训练中心只在第 1、2 行有强信号。

测试竖线移动到第 5、6 列后，它和“训练竖线模板”的列位置几乎对不上，却会在第 1、2 行与“训练横线模板”有少量重叠。距离比较会被这种位置错配误导。测试横线也会发生对称问题。所以这个刻意构造的数据上，raw template accuracy 是 `0.000`。

卷积特征分类器不比较绝对列号。它问的是：整张图任意位置有没有竖线响应？有没有横线响应？因此输出：

```text
RAW_TEMPLATE_ACC=0.000
CONV_FEATURE_ACC=1.000
SHIFT_GENERALIZATION_GAIN=1.000
```

这个结果的边界也要说清楚：它只证明“共享滤波器 + pooling”在这个合成平移任务上解决了位置绑定失败。它不证明真实图片识别已经完成，也不证明任何训练出来的 CNN 都会自然泛化。

## 看报告时先检查这几行

`reports/cnn_report.md` 里每个测试样本都有两类响应。你应该重点看两个条件：

```text
VERTICAL_FILTER_RESPONSE_OK=yes
HORIZONTAL_FILTER_RESPONSE_OK=yes
```

它们分别表示：

- 所有竖线测试样本中，`vertical_response > horizontal_response`。
- 所有横线测试样本中，`horizontal_response > vertical_response`。

如果这两个条件成立，说明方向滤波器确实在机制层面区分了形状方向。再看 `CONV_FEATURE_ACC=1.000`，才能把“特征响应正确”和“最终分类正确”连起来。

## 常见错误

### 1. 把卷积和全连接只看成矩阵乘法

从计算角度，它们都可以被写成矩阵运算；从建模假设看，差别很大。全连接层为每个输入位置保留独立权重，卷积层把同一个局部权重模板复用到不同空间位置。图像任务需要的局部性和平移共享，正是这个结构假设提供的。

### 2. 忽略 padding 后的输出尺寸

3x3 核在没有 padding 的 8x8 图上只会产生 6x6 输出。加 `padding=1` 后才会得到 8x8 输出。公式可以先记成：

```text
out = floor((input + 2 * padding - kernel) / stride) + 1
```

多层网络里尺寸变化会一层层传递，写错一次，后面的 flatten 或 Linear 输入维度就会错。

### 3. 把 pooling 理解成“随便降采样”

max pooling 保留局部最大响应。它牺牲一部分精确位置，换来更稳定的“这个局部特征出现过”的信号。分类任务常常能接受这种取舍；检测、分割、关键点定位等任务对位置更敏感，不能无限制地丢空间信息。

### 4. 看到 100% accuracy 就误以为模型已经强

本实验的数据是人为构造的。100% 说明机制解释成功，不代表真实任务效果好。真实图像任务必须继续检查训练/验证/测试划分、数据增强、类不平衡、过拟合、混淆矩阵、错误样本和 baseline。

## 练习

1. 把测试位置从 `[5, 6]` 改成 `[3, 4, 5, 6]`，观察 raw template 和卷积特征的 accuracy 是否变化。
2. 把噪声强度从 `0.05` 调到 `0.2`，看方向响应差距是否仍然稳定。
3. 去掉 `padding=1`，解释输出尺寸如何变化，边缘位置的响应为什么可能受影响。
4. 把 `max_pool2d(..., size=2, stride=2)` 改成不做 pooling，只取卷积图的 `global_max`，比较报告是否变化。
5. 增加一类“对角线”，手写一个 3x3 对角线检测核，并为它补测试。
6. 进一步改成可学习参数：把两个手写核当作初始化，用交叉熵 loss 和梯度下降学习核权重。

## 继续往下学什么

学完这一篇后，合理的下一步是：

1. 用 PyTorch 的 `nn.Conv2d`、`nn.ReLU`、`nn.MaxPool2d` 重写同一个实验，确认张量维度是 `(N, C, H, W)`。
2. 加入多通道输入和多个输出通道，理解一层卷积为什么会产生一组 feature maps。
3. 接 LeNet/MNIST 级别的小图像分类，但仍保留 majority/linear/MLP baseline。
4. 再进入现代 CNN block、残差连接和视觉 Transformer。每一步都要回到 baseline、数据划分和错误样本，避免只堆模型名。

## 参考资料

- PyTorch `Conv2d` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv2d.html>
- PyTorch `MaxPool2d` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.MaxPool2d.html>
- PyTorch `ReLU` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.ReLU.html>
- Dive into Deep Learning, Convolutional Neural Networks：<https://d2l.ai/chapter_convolutional-neural-networks/index.html>
- Stanford CS231n, Convolutional Neural Networks：<https://cs231n.github.io/convolutional-networks/>
- Goodfellow, Bengio, Courville, *Deep Learning*, Convolutional Networks：<https://www.deeplearningbook.org/contents/convnets.html>
