# -*- coding: utf-8 -*-
"""CIFAR-10 大作业结果摘要。"""
import json
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "results"
m = {k: json.load(open(RES / f"metrics_{k}.json", encoding="utf-8"))
     for k in ["base", "ds", "ds_se", "final"]}
print("=" * 74)
print("课内大作业：基于结构改进的轻量 CNN 图像分类 —— 结果摘要")
print("=" * 74)
print("数据集：CIFAR-10；训练 25000 张，测试 10000 张；训练 8 轮")
print("-" * 74)
print(f"{'模型':<18}{'参数量/M':>10}{'MACs/M':>10}{'准确率':>10}")
for k, name in [("base", "基线 CNN"), ("ds", "深度可分离"), ("ds_se", "DS+SE"), ("final", "DS+SE+GN+GELU")]:
    r = m[k]
    print(f"{name:<18}{r['params_m']:>10.3f}{r['macs_m']:>10.2f}{r['test_acc']*100:>9.2f}%")
print("-" * 74)
print(f"深度可分离：参数降低 {(1-m['ds']['params_m']/m['base']['params_m'])*100:.1f}%，"
      f"MACs 降低 {(1-m['ds']['macs_m']/m['base']['macs_m'])*100:.1f}%，"
      f"准确率 {m['ds']['test_acc']*100:.2f}%")
print(f"SE 注意力：准确率 {m['ds_se']['test_acc']*100:.2f}%")
print(f"最终模型：准确率 {m['final']['test_acc']*100:.2f}%，"
      f"参数量为基线的 {m['final']['params_m']/m['base']['params_m']*100:.1f}%")
print("=" * 74)
