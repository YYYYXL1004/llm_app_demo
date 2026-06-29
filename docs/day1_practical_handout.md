# Day 1 实操讲义：环境配置与 Baseline 跑通

> 本讲义只关注实操：配环境、整理项目、检查数据、运行代码、保存结果、排查常见问题。  
> 今日目标不是追求最高准确率，而是保证每位同学都能跑通一次可复现的 baseline 实验。

---

## 0. 今日完成目标

完成 Day 1 后，你应该能做到：

- 使用 Miniconda 创建独立 Python 环境
- 安装 PyTorch、torchvision、pandas、Pillow 等依赖
- 整理车型分类项目目录
- 检查数据路径和标签文件
- 跑通 baseline 训练脚本
- 保存训练日志和模型权重
- 根据常见报错进行基础 debug

---

## 1. 实验准备

请确认电脑上有以下工具：


| 工具                     | 用途           |
| ---------------------- | ------------ |
| Miniconda              | 管理 Python 环境 |
| VS Code / PyCharm 等编译器 | 查看和编辑代码      |
| 终端 / Anaconda Prompt   | 执行命令         |


miniconda 的安装（win/mac）：建议去查找相关博客教程
例如：[https://blog.csdn.net/ming12131342/article/details/140233867](https://blog.csdn.net/ming12131342/article/details/140233867)

---

## 2. 安装并检查 Miniconda

安装 Miniconda 后，打开终端，输入：

```bash
conda --version
```

如果看到类似：

```bash
conda 24.x.x
```

说明安装成功。

如果提示：

```bash
conda: command not found
```

请尝试：

1. 关闭终端并重新打开；
2. Windows 使用 Anaconda Prompt；
3. 检查 Miniconda 是否安装完成；
4. 必要时重新安装 Miniconda。

---

## 3. 创建课程环境

创建独立环境：

```bash
conda create -n carcls python=3.10 -y
```

激活环境：

```bash
conda activate carcls
```

激活成功后，终端前面通常会出现：

```bash
(carcls)
```

检查 Python：

```bash
python --version
```

建议输出：

```bash
Python 3.10.x
```

---

## 4. 安装依赖

### 4.1 通用 CPU 版本

没有 NVIDIA GPU，或只是先跑通流程，可以安装：

```bash
pip install torch torchvision pandas pillow pyyaml tqdm tensorboard
```

### 4.2 检查 PyTorch

```bash
python -c "import torch; print(torch.__version__)"
python -c "import torch; print(torch.cuda.is_available())"
```

如果第二条输出：

```bash
True
```

说明 PyTorch 可以使用 GPU。

如果输出：

```bash
False
```

也可以继续使用 CPU 跑通流程，只是训练会慢一些。

---

## 5. 安装项目依赖

如果项目中有 `requirements.txt`：

```bash
pip install -r requirements.txt
```

如果没有，可以手动安装：

```bash
pip install torch torchvision pandas pillow pyyaml tqdm tensorboard
```

检查依赖：

```bash
python -c "import torch; print('torch ok')"
python -c "import torchvision; print('torchvision ok')"
python -c "import pandas; print('pandas ok')"
python -c "from PIL import Image; print('Pillow ok')"
```

---

## 6. 快速跑通 baseline

第一次运行不要直接全量训练，先用小数据确认流程：

```bash
python train_simple_cnn.py
```

程序会自动检查数据并开始训练。正常情况下会看到类似输出：

```text
======================================================================
汽车分类训练 
======================================================================
使用设备: cpu
开始时间: 2026-01-01 10:00:00
======================================================================

[1/5] 准备数据...
  训练集: 8144 张
  验证集: 8041 张
  每批: 64 张
  类别数: 196
  每类平均样本: 41.6

[2/5] 创建模型...
  总参数量: 4,523,012

[3/5] 准备训练...
  损失函数: CrossEntropyLoss (label_smoothing=0.1)
  优化器: AdamW (lr=0.001, weight_decay=0.0001)
  调度器: Warmup(3) + CosineAnnealing

[4/5] 开始训练 40 个epoch...
======================================================================
```

然后会逐 epoch 显示训练进度：

```text
Epoch [1/40]
----------------------------------------------------------------------
  Training: 100%|████████████| 128/128 [02:05<00:00, loss=5.234, acc=1.23%]
  Validating: 100%|██████████| 126/126 [00:18<00:00, loss=5.190, acc=2.01%]
  训练  - 损失: 5.2340, 准确率: 1.23%
  验证  - 损失: 5.1900, 准确率: 2.01%
  当前学习率: 0.000333
  本轮耗时: 143.2s
  ★ 新最佳模型已保存！准确率: 2.01%
```

---

## 7. 查看训练结果

训练完成后，会生成：

```text
.
├── train_simple_cnn.log    # 训练日志（包含完整输出）
└── best_model_simple.pth   # 验证集表现最好的模型权重
```

文件说明：


| 文件                      | 作用                 |
| ----------------------- | ------------------ |
| `train_simple_cnn.log`  | 保存所有训练输出（控制台打印的内容） |
| `best_model_simple.pth` | 验证集表现最好的模型权重       |


打开 `train_simple_cnn.log`，能看到完整的训练记录：

```text
======================================================================
汽车分类训练 
======================================================================
使用设备: cpu
...

Epoch [1/40]
  训练  - 损失: 5.2340, 准确率: 1.23%
  验证  - 损失: 5.1900, 准确率: 2.01%
  当前学习率: 0.000333
  本轮耗时: 143.2s
  ★ 新最佳模型已保存！准确率: 2.01%

======================================================================
[5/5] 训练完成！
  最佳验证准确率: 52.34%
  总耗时: 95.2 分钟
  结束时间: 2026-01-01 11:35:00
  模型已保存到: best_model_simple.pth
======================================================================
```

今天至少要确认：

- 程序能训练至少 1 个 epoch；
- 日志文件能保存；
- `best_model_simple.pth` 能保存；
- 训练过程中没有中断报错。

---

## 8. 模型推理

训练完成后，可以用推理脚本验证模型效果：

```bash
python inference_simple_cnn.py
```

输出类似：

```text
使用设备: cpu
模型参数量: 4,523,012

开始评估 8041 张验证图片...
  已评估 500/8041 张，当前准确率: 51.23%
  已评估 1000/8041 张，当前准确率: 51.89%
  ...

==================================================
验证集最终准确率: 52.34% (4209/8041)
==================================================
```

---

## 9. 今日提交内容


| 提交内容                   | 要求                        |
| ---------------------- | ------------------------- |
| 环境检查截图                 | 能看到 Python / PyTorch 检查结果 |
| 训练运行截图                 | 能看到至少 1 个 epoch 的输出       |
| `train_simple_cnn.log` | 保存训练日志                    |


---

## 10. 常用命令汇总

```bash
# 查看 conda 版本
conda --version

# 创建环境
conda create -n carcls python=3.10 -y

# 激活环境
conda activate carcls

# 查看 Python 版本
python --version

# 安装依赖
pip install torch torchvision pandas pillow pyyaml tqdm tensorboard

# 检查 PyTorch
python -c "import torch; print(torch.__version__)"

# 检查 GPU
python -c "import torch; print(torch.cuda.is_available())"

# 进入项目目录
cd classfication_car

# 训练模型
python train_simple_cnn.py

# 推理验证
python inference_simple_cnn.py
```

---

## 11. 代码结构说明

本项目的代码结构：

```text
classfication_car/
├── train_simple_cnn.py       # 训练脚本（含模型定义、数据加载、训练循环）
├── inference_simple_cnn.py   # 推理脚本（在验证集上评估准确率）
└── data/                     # 数据目录
    ├── train/                # 训练图片
    ├── val/                  # 验证图片
    ├── train_labels.csv      # 训练集标签文件
    └── val_labels.csv        # 验证集标签文件
```

### 训练脚本核心组件


| 组件                    | 行数参考    | 功能                    |
| --------------------- | ------- | --------------------- |
| Logger                | 31-54   | 同时输出到终端和文件的日志器        |
| Config                | 61-85   | 集中管理所有超参数             |
| CarDataset            | 92-121  | PyTorch 数据集封装         |
| train_transform       | 132-156 | 训练时数据增强（翻转、旋转、颜色抖动等）  |
| val_transform         | 159-164 | 验证时预处理（无增强）           |
| SimpleCNN             | 196-252 | 改进版 CNN 模型（4个卷积块+GAP） |
| WarmupCosineScheduler | 274-313 | 学习率调度（预热+余弦退火）        |
| train_epoch           | 327-377 | 单 epoch 训练函数          |
| validate              | 387-418 | 验证函数                  |
| main                  | 425-548 | 主训练流程                 |


