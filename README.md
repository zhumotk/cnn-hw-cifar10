# CIFAR-10 CNN 结构改进实验

代码仓库：<https://github.com/zhumotk/cnn-hw-cifar10>

课内大作业：在 CIFAR-10 上实现一个 VGG 式经典 CNN，并从深度可分离卷积、SE 通道注意力、GroupNorm/GELU 三个方向做结构改进与消融对比。

## 模型

| 模型 | 说明 |
|---|---|
| `base` | 标准 3×3 卷积 + BatchNorm + ReLU |
| `ds` | 深度可分离卷积替代标准卷积 |
| `ds_se` | 深度可分离卷积 + SE 通道注意力 |
| `final` | 深度可分离 + SE + GroupNorm + GELU |

## 数据与训练

- 数据集：CIFAR-10（10 类，32×32 彩色图像）
- 训练集：从 50,000 张训练图中固定随机抽取 25,000 张
- 测试集：10,000 张
- 数据增强：RandomCrop(32, padding=4) + RandomHorizontalFlip
- 优化器：SGD，momentum=0.9，weight_decay=5e-4
- 学习率：0.05，余弦退火
- batch size：256，epochs：8

## 运行

```bash
pip install -r requirements.txt

# 首次运行会自动下载 CIFAR-10 到 data/；也可手动放置 cifar-10-python.tar.gz
python code/train_cnn.py --model base --epochs 8 --batch 256 --train_size 25000
python code/train_cnn.py --model ds --epochs 8 --batch 256 --train_size 25000
python code/train_cnn.py --model ds_se --epochs 8 --batch 256 --train_size 25000
python code/train_cnn.py --model final --epochs 8 --batch 256 --train_size 25000

python code/make_figures.py
```

## 结果

| 模型 | 参数量 / M | MACs / M | 测试准确率 |
|---|---:|---:|---:|
| base | 1.176 | 52.79 | 81.02% |
| ds | 0.142 | 6.58 | 69.82% |
| ds_se | 0.165 | 6.60 | 70.33% |
| final (DS+SE+GN+GELU) | 0.165 | 6.60 | 57.51% |

训练结束后见 `results/metrics_*.json` 与报告中的表格。所有数字由脚本输出并写入 JSON，报告中的数值直接读取这些文件。

结论：深度可分离卷积把参数量降低约 87.9%、MACs 降低约 87.5%，但相同 8 轮训练预算下精度下降；SE 只能恢复少量精度；GroupNorm/GELU 组合在短训练下收敛困难。综合考虑，推荐 DS+SE 作为轻量方案，最终报告中有详细分析。

## 目录

```
code/     训练与绘图脚本
data/     CIFAR-10（不提交到 Git）
results/  指标、权重、日志和图表（权重不提交到 Git）
```

## 说明

本作业与课内实验三使用不同的网络结构、数据集和训练设置。完整实验分析见课程设计报告。
