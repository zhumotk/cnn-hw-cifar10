# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RES = Path(__file__).resolve().parent.parent / "results"
FONT = r"C:\Windows\Fonts\simhei.ttf"
MONO = r"C:\Windows\Fonts\consola.ttf"
lines = [l.rstrip() for l in open(RES / "summary.txt", encoding="utf-8").read().replace("\r", "").split("\n") if l.strip()]
font = ImageFont.truetype(FONT, 21)
mono = ImageFont.truetype(MONO, 20)
small = ImageFont.truetype(FONT, 15)
W, lh, top = 1400, 34, 82
H = top + lh * len(lines) + 38
img = Image.new("RGB", (W, H), "#0c0c0c")
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 56], fill="#202020")
for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
    d.ellipse([22 + i * 28, 19, 38 + i * 28, 35], fill=c)
d.text((130, 14), "命令提示符  —  python make_summary.py", font=small, fill="#cccccc")
y = top
for ln in lines:
    color = "#d4d4d4"
    if ln.startswith("="):
        color = "#4ec9b0"
    elif "%" in ln:
        color = "#b5cea8"
    elif ln.startswith("模型") or ln.startswith("数据集"):
        color = "#9cdcfe"
    use_mono = all(ord(c) < 128 for c in ln)
    d.text((28, y), ln, font=(mono if use_mono else font), fill=color)
    y += lh
img.save(RES / "console_result.png")
print("saved", img.size)
