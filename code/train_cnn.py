# -*- coding: utf-8 -*-
"""
课内大作业：CIFAR-10 经典 CNN 的结构改进
模型：
  base   : VGG 式 CNN（标准 3×3 卷积 + BN + ReLU）
  ds     : 深度可分离卷积替代标准卷积
  ds_se  : 深度可分离卷积 + SE 通道注意力
  final  : 深度可分离卷积 + SE + GroupNorm + GELU
"""
import os
import json
import time
import random
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
import torchvision
import torchvision.transforms as T
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
RES = BASE / "results"
RES.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(8)


def make_norm(ch, kind):
    if kind == "gn":
        return nn.GroupNorm(min(8, ch), ch)
    return nn.BatchNorm2d(ch)


def make_act(kind):
    return nn.GELU() if kind == "gelu" else nn.ReLU(inplace=True)


class ConvBlock(nn.Module):
    def __init__(self, cin, cout, norm="bn", act="relu", separable=False):
        super().__init__()
        if separable:
            self.conv = nn.Sequential(
                nn.Conv2d(cin, cin, 3, 1, 1, groups=cin, bias=False),
                make_norm(cin, norm), make_act(act),
                nn.Conv2d(cin, cout, 1, bias=False),
                make_norm(cout, norm), make_act(act),
            )
        else:
            self.conv = nn.Sequential(
                nn.Conv2d(cin, cout, 3, 1, 1, bias=False),
                make_norm(cout, norm), make_act(act),
            )

    def forward(self, x):
        return self.conv(x)


class SEBlock(nn.Module):
    def __init__(self, ch, reduction=8):
        super().__init__()
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(ch, max(4, ch // reduction), 1), nn.ReLU(inplace=True),
            nn.Conv2d(max(4, ch // reduction), ch, 1), nn.Sigmoid(),
        )

    def forward(self, x):
        return x * self.fc(x)


class SmallCNN(nn.Module):
    def __init__(self, separable=False, use_se=False, norm="bn", act="relu"):
        super().__init__()
        widths = [32, 64, 128, 256]
        blocks = []
        cin = 3
        for i, w in enumerate(widths):
            blocks.append(ConvBlock(cin, w, norm, act, separable))
            blocks.append(ConvBlock(w, w, norm, act, separable))
            if use_se:
                blocks.append(SEBlock(w))
            blocks.append(nn.MaxPool2d(2))
            cin = w
        self.features = nn.Sequential(*blocks)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(256, 10)

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x).flatten(1)
        return self.classifier(x)


def build_model(kind):
    if kind == "base":
        return SmallCNN(False, False, "bn", "relu")
    if kind == "ds":
        return SmallCNN(True, False, "bn", "relu")
    if kind == "ds_se":
        return SmallCNN(True, True, "bn", "relu")
    if kind == "final":
        return SmallCNN(True, True, "gn", "gelu")
    raise ValueError(kind)


def count_params(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


@torch.no_grad()
def count_macs(model, input_size=(1, 3, 32, 32)):
    """统计乘加次数（MACs），单位 M。"""
    macs = [0]
    hooks = []

    def hook_conv(m, inp, out):
        # 输出元素数 × (kernel^2 × in_channels/groups)
        k = m.kernel_size[0] * m.kernel_size[1]
        macs[0] += out.numel() * k * (m.in_channels // m.groups)

    def hook_linear(m, inp, out):
        macs[0] += out.numel() * m.in_features

    for m in model.modules():
        if isinstance(m, nn.Conv2d):
            hooks.append(m.register_forward_hook(hook_conv))
        elif isinstance(m, nn.Linear):
            hooks.append(m.register_forward_hook(hook_linear))
    model.eval()
    model(torch.zeros(*input_size))
    for h in hooks:
        h.remove()
    return macs[0] / 1e6


def get_loaders(batch, train_size, workers=0):
    mean = (0.4914, 0.4822, 0.4465)
    std = (0.2470, 0.2435, 0.2616)
    train_tf = T.Compose([
        T.RandomCrop(32, padding=4),
        T.RandomHorizontalFlip(),
        T.ToTensor(),
        T.Normalize(mean, std),
    ])
    test_tf = T.Compose([T.ToTensor(), T.Normalize(mean, std)])
    train = torchvision.datasets.CIFAR10(DATA, train=True,
                                         download=not (DATA / "cifar-10-batches-py").exists(),
                                         transform=train_tf)
    test = torchvision.datasets.CIFAR10(DATA, train=False,
                                        download=not (DATA / "cifar-10-batches-py").exists(),
                                        transform=test_tf)
    if train_size and train_size < len(train):
        g = torch.Generator().manual_seed(42)
        idx = torch.randperm(len(train), generator=g)[:train_size].tolist()
        train = Subset(train, idx)
    return (DataLoader(train, batch, shuffle=True, num_workers=workers, drop_last=True),
            DataLoader(test, 256, shuffle=False, num_workers=workers), test)


def evaluate(model, loader):
    model.eval()
    correct, total, loss_sum = 0, 0, 0.0
    ce = nn.CrossEntropyLoss()
    all_pred, all_true = [], []
    with torch.no_grad():
        for x, y in loader:
            out = model(x)
            loss_sum += ce(out, y).item() * x.size(0)
            pred = out.argmax(1)
            correct += (pred == y).sum().item()
            total += x.size(0)
            all_pred.append(pred.numpy())
            all_true.append(y.numpy())
    return correct / total, loss_sum / total, np.concatenate(all_pred), np.concatenate(all_true)


def train(kind, epochs, batch, lr, train_size):
    set_seed(42)
    train_loader, test_loader, test_ds = get_loaders(batch, train_size)
    model = build_model(kind)
    params = count_params(model)
    macs = count_macs(model)
    print("=" * 74)
    print(f"模型 {kind} | 参数 {params/1e6:.3f} M | MACs {macs:.2f} M | 训练样本 {len(train_loader.dataset)}")
    print(f"epochs={epochs} batch={batch} lr={lr}", flush=True)
    ce = nn.CrossEntropyLoss()
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=5e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    hist = {"train_loss": [], "test_acc": [], "test_loss": []}
    best_acc, best_state = 0.0, None
    t0 = time.time()
    for ep in range(1, epochs + 1):
        model.train()
        run_loss, n = 0.0, 0
        for x, y in train_loader:
            opt.zero_grad()
            out = model(x)
            loss = ce(out, y)
            loss.backward()
            opt.step()
            run_loss += loss.item() * x.size(0)
            n += x.size(0)
        sched.step()
        train_loss = run_loss / n
        acc, test_loss, pred, true = evaluate(model, test_loader)
        hist["train_loss"].append(train_loss)
        hist["test_acc"].append(acc)
        hist["test_loss"].append(test_loss)
        if acc > best_acc:
            best_acc = acc
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            torch.save({"model": kind, "state": best_state, "acc": acc}, RES / f"cnn_{kind}.pt")
        if ep == 1 or ep % 2 == 0:
            print(f"Epoch {ep:2d}/{epochs} | train_loss={train_loss:.4f} | "
                  f"test_acc={acc*100:.2f}% | test_loss={test_loss:.4f} | {time.time()-t0:.1f}s", flush=True)
    model.load_state_dict(best_state)
    acc, test_loss, pred, true = evaluate(model, test_loader)
    np.savez(RES / f"pred_{kind}.npz", pred=pred, true=true)
    out = {"model": kind, "params_m": params / 1e6, "macs_m": macs,
           "epochs": epochs, "batch": batch, "lr": lr, "train_size": len(train_loader.dataset),
           "best_test_acc": best_acc, "test_acc": acc, "test_loss": test_loss,
           "train_time_s": time.time() - t0, "history": hist}
    (RES / f"metrics_{kind}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("-" * 74)
    print(f"{kind} 完成：best_acc={best_acc*100:.2f}% | test_acc={acc*100:.2f}% | "
          f"params={params/1e6:.3f}M | MACs={macs:.2f}M | {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="base", choices=["base", "ds", "ds_se", "final"])
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch", type=int, default=128)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--train_size", type=int, default=25000)
    args = parser.parse_args()
    train(args.model, args.epochs, args.batch, args.lr, args.train_size)
