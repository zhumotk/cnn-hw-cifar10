# -*- coding: utf-8 -*-
"""生成 CIFAR-10 大作业结果图。"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

BASE = Path(__file__).resolve().parent.parent
RES = BASE / "results"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
NAMES = {"base": "基线 CNN", "ds": "深度可分离", "ds_se": "DS+SE", "final": "DS+SE+GN+GELU"}
COLORS = {"base": "#718096", "ds": "#2b6cb0", "ds_se": "#2f855a", "final": "#c53030"}

m = {k: json.load(open(RES / f"metrics_{k}.json", encoding="utf-8")) for k in NAMES}

# 曲线
fig, axes = plt.subplots(1, 2, figsize=(11, 4), dpi=200)
for k in NAMES:
    axes[0].plot(m[k]["history"]["train_loss"], label=NAMES[k], color=COLORS[k], lw=1.6)
    axes[1].plot([a * 100 for a in m[k]["history"]["test_acc"]], label=NAMES[k], color=COLORS[k], lw=1.6)
axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("训练损失")
axes[0].set_title("(a) 训练损失"); axes[0].grid(alpha=0.3, ls="--")
axes[0].legend(frameon=False, fontsize=7)
axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("测试准确率 / %")
axes[1].set_title("(b) 测试准确率"); axes[1].grid(alpha=0.3, ls="--")
axes[1].legend(frameon=False, fontsize=7)
plt.tight_layout(); plt.savefig(RES / "curves.png", bbox_inches="tight"); plt.close()

# 参数/MACs-精度
fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.9), dpi=200)
for ax, key, label in [(axes[0], "params_m", "参数量 / M"), (axes[1], "macs_m", "MACs / M")]:
    xs = [m[k][key] for k in NAMES]
    ys = [m[k]["test_acc"] * 100 for k in NAMES]
    for k, x, y in zip(NAMES, xs, ys):
        ax.scatter(x, y, s=70, color=COLORS[k], zorder=3)
        ax.annotate(NAMES[k], (x, y), textcoords="offset points", xytext=(5, 5), fontsize=7)
    ax.set_xlabel(label); ax.set_ylabel("测试准确率 / %")
    ax.grid(alpha=0.3, ls="--")
axes[0].set_title("(a) 参数量与准确率")
axes[1].set_title("(b) 计算量与准确率")
plt.tight_layout(); plt.savefig(RES / "efficiency.png", bbox_inches="tight"); plt.close()

# 混淆矩阵
p = np.load(RES / "pred_final.npz")
cm = confusion_matrix(p["true"], p["pred"], labels=list(range(10)))
cmn = cm / cm.sum(axis=1, keepdims=True)
fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=200)
im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(10)); ax.set_yticks(range(10))
ax.set_xticklabels(CLASSES, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(CLASSES, fontsize=8)
ax.set_xlabel("预测类别"); ax.set_ylabel("真实类别")
for i in range(10):
    for j in range(10):
        if cmn[i, j] > 0.01:
            ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center",
                    fontsize=6.5, color="white" if cmn[i, j] > 0.55 else "#222")
plt.colorbar(im, fraction=0.046, pad=0.04)
plt.tight_layout(); plt.savefig(RES / "confusion.png", bbox_inches="tight"); plt.close()

# 模型结构示意图（简单框图）
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
fig, ax = plt.subplots(figsize=(11, 2.8), dpi=200)
ax.set_xlim(0, 11); ax.set_ylim(0, 2.8); ax.axis("off")
blocks = [("输入\n32×32×3", 0.2), ("Stage1\n32×32", 1.9), ("Stage2\n64×16", 3.6),
          ("Stage3\n128×8", 5.3), ("Stage4\n256×4", 7.0), ("GAP\n256", 8.7), ("FC\n10", 10.0)]
for text, x in blocks:
    w = 1.25 if x < 9.5 else 0.75
    ax.add_patch(FancyBboxPatch((x, 0.8), w, 1.0, boxstyle="round,pad=0.02,rounding_size=0.06",
                                edgecolor="#2b6cb0", facecolor="#ebf4ff", lw=1.2))
    ax.text(x + w / 2, 1.3, text, ha="center", va="center", fontsize=8.5)
for x1, x2 in [(1.45, 1.9), (3.15, 3.6), (4.85, 5.3), (6.55, 7.0), (8.25, 8.7), (9.95, 10.0)]:
    ax.add_patch(FancyArrowPatch((x1, 1.3), (x2, 1.3), arrowstyle="-|>", mutation_scale=11, lw=1.1, color="#4a5568"))
ax.text(5.5, 2.35, "VGG 式 SmallCNN：每个 Stage 含 2 个卷积块，可替换为深度可分离卷积并插入 SE",
        ha="center", fontsize=9.5)
plt.tight_layout(); plt.savefig(RES / "arch.png", bbox_inches="tight", facecolor="white"); plt.close()
print("figures saved")
