# -*- coding: utf-8 -*-
"""生成课内大作业报告 DOCX。"""
import os
import json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
OUT = os.path.join(BASE, "课内大作业报告_基于结构改进的轻量CNN图像分类.docx")
m = {k: json.load(open(os.path.join(RES, f"metrics_{k}.json"), encoding="utf-8"))
     for k in ["base", "ds", "ds_se", "final"]}
P = lambda x: f"{x*100:.2f}%"
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x59, 0x59, 0x59)
ACCENT = RGBColor(0x1F, 0x4E, 0x79)


def run(p, text, size=12, bold=False, cn="宋体", en="Times New Roman", color=BLACK, italic=False):
    r = p.add_run(text)
    r.font.name = en; r.font.size = Pt(size); r.bold = bold; r.italic = italic
    r.font.color.rgb = color
    r._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), cn)
    return r


def para(text="", indent=True, before=0, after=6, line=1.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    p.paragraph_format.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    if text:
        run(p, text)
    return p


def bullet(text):
    p = para(indent=False, after=4)
    p.paragraph_format.left_indent = Cm(0.74)
    p.paragraph_format.first_line_indent = Cm(-0.37)
    run(p, "• " + text)
    return p


def heading(text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if level == 1:
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(10)
        run(p, text, 16, True, "黑体", "Arial", ACCENT)
    elif level == 2:
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(6)
        run(p, text, 13.5, True, "黑体", "Arial")
    else:
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        run(p, text, 12, True, "黑体", "Arial")
    p.paragraph_format.keep_with_next = True
    return p


def formula(text):
    p = para(indent=False, before=3, after=5, line=1.25, align=WD_ALIGN_PARAGRAPH.CENTER)
    run(p, text, 11.5, en="Cambria Math")


def caption(text):
    p = para(indent=False, before=3, after=9, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
    run(p, text, 10, color=GRAY)


def figure(path, width, cap):
    p = para(indent=False, before=6, after=2, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
    p.add_run().add_picture(path, width=Cm(width))
    caption(cap)


def keep_table(t):
    for i, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if i < len(t.rows) - 1:
            for cell in row.cells:
                for pp in cell.paragraphs:
                    pp.paragraph_format.keep_with_next = True


def table(headers, rows, widths, fs=9.5):
    if doc.paragraphs:
        doc.paragraphs[-1].paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for j, w in enumerate(widths):
        for cell in t.columns[j].cells:
            cell.width = Cm(w)
    for j, h in enumerate(headers):
        cell = t.cell(0, j); cell.text = ""
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, h, fs, True)
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "DCE6F1")
        tcPr.append(shd)
    for i, row in enumerate(rows, 1):
        for j, val in enumerate(row):
            cell = t.cell(i, j); cell.text = ""
            p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run(p, str(val), fs)
    keep_table(t)
    caption("")


def code_block(code, title):
    p = para(indent=False, before=6, after=2, align=WD_ALIGN_PARAGRAPH.LEFT)
    run(p, title, 9.5, bold=True, color=GRAY)
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    cell = t.cell(0, 0); cell.width = Cm(15.2)
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "F5F5F5")
    tcPr.append(shd)
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "D0D0D0"); borders.append(el)
    tcPr.append(borders)
    first = True
    for line in code.strip("\n").split("\n"):
        pp = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        pp.paragraph_format.space_before = Pt(0)
        pp.paragraph_format.space_after = Pt(0)
        pp.paragraph_format.line_spacing = 1.0
        run(pp, line if line else " ", 8.3, en="Consolas")
    keep_table(t)
    para(indent=False, before=0, after=0, line=1.0)


def page_num(p):
    r = p.add_run()
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "separate")
    tt = OxmlElement("w:t"); tt.text = "1"
    f3 = OxmlElement("w:fldChar"); f3.set(qn("w:fldCharType"), "end")
    for el in (f1, it, f2, tt, f3):
        r._r.append(el)
    r.font.size = Pt(9); r.font.color.rgb = GRAY


def hrule(p):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "4")
    b.set(qn("w:space"), "1"); b.set(qn("w:color"), "BFBFBF")
    pBdr.append(b); pPr.append(pBdr)


# ----------------------------- 文档 -----------------------------
doc = Document()
doc.core_properties.title = "基于结构改进的轻量CNN图像分类"
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = Cm(2.54); sec.bottom_margin = Cm(2.54)
sec.left_margin = Cm(2.8); sec.right_margin = Cm(2.6)
sec.header_distance = Cm(1.4); sec.footer_distance = Cm(1.3)
sec.different_first_page_header_footer = True
st = doc.styles["Normal"]
st.font.name = "Times New Roman"; st.font.size = Pt(12)
st._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

hp = sec.header.paragraphs[0]
hp.text = "《深度学习》课内大作业报告"
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
for r in hp.runs:
    r.font.size = Pt(9); r.font.color.rgb = GRAY
hrule(hp)
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
page_num(fp)

# 封面
for _ in range(2):
    doc.add_paragraph()
p = para(indent=False, after=4, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
run(p, "《深度学习》课内大作业", 16, color=GRAY)
p = para(indent=False, before=22, after=6, line=1.15, align=WD_ALIGN_PARAGRAPH.CENTER)
run(p, "基于结构改进的\n轻量 CNN 图像分类", 26, True, "黑体", "Arial", ACCENT)
p = para(indent=False, before=8, after=4, line=1.2, align=WD_ALIGN_PARAGRAPH.CENTER)
run(p, "——CIFAR-10 上的经典 CNN 复现、改进与场景应用", 13)
p = para(indent=False, before=2, after=0, line=1.2, align=WD_ALIGN_PARAGRAPH.CENTER)
run(p, "深度可分离卷积 · SE 注意力 · GroupNorm/GELU", 10.5, color=GRAY)
for _ in range(3):
    doc.add_paragraph()
info = [("姓　　名", "________________"), ("学　　号", "________________"),
        ("班　　级", "________________"), ("专　　业", "________________"),
        ("指导教师", "________________"), ("完成日期", "2026 年 11 月")]
t = doc.add_table(rows=len(info), cols=2)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (k, v) in enumerate(info):
    for j in range(2):
        cell = t.cell(i, j); cell.width = Cm(4.2 if j == 0 else 7.2)
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j == 0 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(4)
        run(p, k + "：" if j == 0 else v, 12, color=BLACK if j == 0 else GRAY)
for _ in range(3):
    doc.add_paragraph()
p = para(indent=False, after=0, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
run(p, "2026 年 11 月", 12, color=GRAY)

# 摘要
doc.add_page_break()
p = para(indent=False, before=0, after=10, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
run(p, "摘　要", 16, True, "黑体", "Arial", ACCENT)
para(f"本作业在公开 CIFAR-10 数据集上实现了一个 VGG 式经典 CNN，并以该网络为基线，从深度可分离卷积、SE 通道注意力和 GroupNorm/GELU 三个方向进行结构改进。"
     "实验从 50,000 张训练图像中固定抽取 25,000 张用于训练，10,000 张测试图像用于评价，统一训练 8 轮。"
     f"基线 CNN 参数量 {m['base']['params_m']:.3f} M、MACs {m['base']['macs_m']:.2f} M，测试准确率 {P(m['base']['test_acc'])}；"
     f"深度可分离卷积把参数量降到 {m['ds']['params_m']:.3f} M、MACs 降到 {m['ds']['macs_m']:.2f} M，测试准确率 {P(m['ds']['test_acc'])}；"
     f"加入 SE 后准确率为 {P(m['ds_se']['test_acc'])}；进一步把 BatchNorm/ReLU 换成 GroupNorm/GELU 后准确率降至 {P(m['final']['test_acc'])}，"
     "说明该组合在 8 轮短训练下收敛困难，不宜作为最终方案。"
     f"综合精度与复杂度，本作业推荐 DS+SE 作为轻量模型：参数量仅为基线的 {m['ds_se']['params_m']/m['base']['params_m']*100:.1f}%，"
     f"MACs 为基线的 {m['ds_se']['macs_m']/m['base']['macs_m']*100:.1f}%，测试准确率 {P(m['ds_se']['test_acc'])}。")

# 1
heading("1  作业任务与总体方案", 1)
heading("1.1  任务理解", 2)
para("大作业要求实现一个经典 CNN 架构，在开源数据集上训练并达到基准准确率；在此基础上进行结构修改，比较参数量、计算量和精度，"
     "并将改进后的模型应用到具体场景。本作业选择图像分类任务，因为它是 CNN 最经典、评价体系最成熟的应用，便于进行结构消融和指标对比。")
para("本作业选用 CIFAR-10 作为开源数据集，基线网络为 VGG 式 SmallCNN：每个 Stage 包含两个 3×3 卷积块，经过 4 次下采样后使用全局平均池化和全连接层分类。"
     "该网络结构清晰、易于修改，适合分析卷积类型、注意力和归一化方式的影响。")
heading("1.2  与课内实验三的区别", 2)
para("本作业与课内实验三使用不同的网络结构、数据集和训练设置：实验三侧重基础 CNN 的搭建与训练流程，本作业则从经典 VGG 式 CNN 出发，"
     "系统比较深度可分离卷积、SE 注意力和 GroupNorm/GELU 三种结构修改对参数量、计算量和准确率的影响，并给出边缘设备场景下的应用分析。"
     "因此，本作业不是对实验三的重复，而是在其基础上进行结构级改进与消融研究。")
heading("1.3  技术路线", 2)
para("技术路线如下：")
bullet("在 CIFAR-10 上实现 VGG 式基线 CNN，固定数据划分、数据增强、优化器和训练轮次；")
bullet("用深度可分离卷积替换标准 3×3 卷积，比较参数量、MACs 和准确率；")
bullet("在深度可分离网络中插入 SE 通道注意力，分析注意力对精度的补偿作用；")
bullet("在 SE 网络中使用 GroupNorm 替代 BatchNorm、GELU 替代 ReLU，得到最终模型；")
bullet("绘制训练曲线、效率散点图和混淆矩阵，分析改进效果、失败类别和场景适用性。")

# 2
heading("2  经典 CNN 与数据集", 1)
heading("2.1  VGG 式基线网络", 2)
para("基线网络由 4 个 Stage 组成，通道数依次为 32、64、128、256。每个 Stage 包含两个 3×3 卷积（padding=1）、BatchNorm 和 ReLU，"
     "最后接 2×2 最大池化，使特征图尺寸从 32×32 逐级降到 4×4。分类头使用全局平均池化和 10 维全连接层。"
     "网络结构如图 1 所示。")
figure(os.path.join(RES, "arch.png"), 15.2, "图 1  VGG 式 SmallCNN 结构")
para(f"基线模型共有 {m['base']['params_m']:.3f} M 参数、{m['base']['macs_m']:.2f} M MACs。"
     "选择该规模而不是 ResNet-18 等更大模型，是为了在 CPU 上完成多次消融训练，同时保留经典 CNN 的“卷积—池化—全连接”结构特征。")

heading("2.2  CIFAR-10 数据集", 2)
para("CIFAR-10 包含 10 类、共 60,000 张 32×32 彩色图像，其中 50,000 张训练、10,000 张测试。类别为飞机、汽车、鸟、猫、鹿、狗、青蛙、马、船、卡车。"
     "本作业从训练集中固定随机抽取 25,000 张用于训练，官方 10,000 张测试图像用于评价。训练阶段使用 RandomCrop(32, padding=4) 和随机水平翻转，"
     "测试阶段只做标准化。")
para("数据划分和随机种子固定为 42，四个模型使用完全相同的训练/测试集，保证比较公平。")

# 3
heading("3  结构改进设计", 1)
heading("3.1  深度可分离卷积", 2)
para("标准 3×3 卷积在每个输出通道上同时进行空间卷积和通道混合，计算量为：")
formula("MACs_std = H × W × C_in × C_out × 9")
para("深度可分离卷积把它拆成深度卷积和逐点卷积：深度卷积对每个输入通道单独做 3×3 空间卷积，逐点卷积用 1×1 卷积完成通道混合。计算量为：")
formula("MACs_ds = H × W × C_in × 9 + H × W × C_in × C_out")
para("当 C_out 较大时，深度可分离卷积的乘加次数显著低于标准卷积。本作业把每个 Stage 中的两个标准卷积都替换为“深度卷积 + 逐点卷积”，"
     "每个子卷积后接归一化和激活函数，通道数与基线保持一致。")

heading("3.2  SE 通道注意力", 2)
para("SE 模块通过全局平均池化获得每个通道的全局响应，再经过两层全连接（本作业用 1×1 卷积实现）和 Sigmoid 得到通道权重：")
formula("s = σ(W_2 · δ(W_1 · GAP(F)))")
formula("F' = s ⊙ F")
para("其中 δ 为 ReLU，σ 为 Sigmoid，⊙ 为逐元素相乘。SE 模块让网络自适应地强调重要通道、抑制无关通道。"
     "本作业在每个 Stage 的两个卷积块之后、池化之前插入 SE，压缩比设为 8。")

heading("3.3  GroupNorm 与 GELU", 2)
para("BatchNorm 依赖 batch 统计量，在小 batch 或分布变化时可能不稳定；GroupNorm 将通道分组后在组内归一化，不依赖 batch 大小。"
     "本作业将最终模型的 BatchNorm 替换为 GroupNorm（每组 8 个通道），以观察归一化方式对训练的影响。"
     "同时把 ReLU 替换为 GELU：")
formula("GELU(x) = x · Φ(x)")
para("其中 Φ(x) 为标准正态分布的累积分布函数。GELU 在零点附近更平滑，理论上可以缓解神经元死亡问题。")

heading("3.4  四个对比模型", 2)
para("四个模型的结构配置如表 1 所示。base 为基线；ds 只替换卷积类型；ds_se 在 ds 上加入 SE；final 在 ds_se 上替换归一化和激活函数。")
caption("表 1  四个对比模型")
table(["模型", "卷积类型", "归一化", "激活函数", "SE 注意力"],
      [["base", "标准 3×3", "BatchNorm", "ReLU", "×"],
       ["ds", "深度可分离", "BatchNorm", "ReLU", "×"],
       ["ds_se", "深度可分离", "BatchNorm", "ReLU", "√"],
       ["final", "深度可分离", "GroupNorm", "GELU", "√"]],
      [3.0, 4.0, 3.6, 3.2, 3.2], 9.5)

# 4
heading("4  实验设置", 1)
heading("4.1  训练参数", 2)
para("四个模型使用相同的训练参数：SGD 优化器，momentum=0.9，weight decay=5×10⁻⁴，初始学习率 0.05，余弦退火，batch size 256，训练 8 轮。"
     "损失函数为交叉熵。实验在 CPU 上完成，软件环境如表 2 所示。")
caption("表 2  实验环境")
table(["项目", "配置 / 版本"],
      [["处理器", "Intel Core i7-14650HX（24 逻辑处理器）"],
       ["内存", "16 GB"],
       ["显卡", "无可用 CUDA，使用 CPU"],
       ["操作系统", "Windows 11（64 位）"],
       ["Python", "3.12.7"],
       ["PyTorch / Torchvision", "2.5.1 / 0.20.1"],
       ["主要依赖", "NumPy、Matplotlib、scikit-learn"]],
      [4.0, 11.0], 9.5)
heading("4.2  评价指标", 2)
para("采用测试集分类准确率作为精度指标：")
formula("Accuracy = 正确分类样本数 / 测试样本总数")
para("采用参数量（Params）和乘加次数（MACs）衡量模型复杂度。参数量由 PyTorch 统计，MACs 通过前向 hook 统计每个卷积层和全连接层的乘加次数，"
     "输入尺寸为 1×3×32×32。MACs 越小，模型在边缘设备上的理论计算开销越低。")

# 5
heading("5  实验结果与分析", 1)
heading("5.1  准确率与复杂度", 2)
para("四个模型在 CIFAR-10 测试集上的结果如表 3 所示。基线 CNN 的测试准确率为 " + P(m['base']['test_acc']) + "，作为本实验的基准。"
     "深度可分离卷积把参数量从 " + f"{m['base']['params_m']:.3f} M 降到 {m['ds']['params_m']:.3f} M，MACs 从 "
     f"{m['base']['macs_m']:.2f} M 降到 {m['ds']['macs_m']:.2f} M，但准确率下降到 {P(m['ds']['test_acc'])}，说明轻量化会带来精度损失。"
     f"加入 SE 后准确率回升到 {P(m['ds_se']['test_acc'])}，但只恢复了一小部分；进一步使用 GroupNorm 和 GELU 后准确率降到 {P(m['final']['test_acc'])}，"
     "说明该归一化/激活组合在 8 轮训练预算下收敛明显更慢。综合精度和复杂度，DS+SE 是本实验更合适的轻量方案。")
caption("表 3  四个模型的准确率、参数量与计算量")
table(["模型", "参数量 / M", "MACs / M", "测试准确率", "相对基线"],
      [["base", f"{m['base']['params_m']:.3f}", f"{m['base']['macs_m']:.2f}", P(m['base']['test_acc']), "—"],
       ["ds", f"{m['ds']['params_m']:.3f}", f"{m['ds']['macs_m']:.2f}", P(m['ds']['test_acc']),
        f"{(m['ds']['test_acc']-m['base']['test_acc'])*100:+.2f} pp"],
       ["ds_se", f"{m['ds_se']['params_m']:.3f}", f"{m['ds_se']['macs_m']:.2f}", P(m['ds_se']['test_acc']),
        f"{(m['ds_se']['test_acc']-m['base']['test_acc'])*100:+.2f} pp"],
       ["final", f"{m['final']['params_m']:.3f}", f"{m['final']['macs_m']:.2f}", P(m['final']['test_acc']),
        f"{(m['final']['test_acc']-m['base']['test_acc'])*100:+.2f} pp"]],
      [2.8, 3.4, 3.2, 3.4, 3.2], 9.5)
figure(os.path.join(RES, "efficiency.png"), 15.0, "图 2  参数量/计算量与测试准确率的关系")

heading("5.2  训练曲线", 2)
para("四个模型的训练损失和测试准确率曲线如图 3 所示。基线在前几轮收敛最快，最终达到最高准确率；深度可分离模型训练损失下降稍慢，"
     "在相同轮次下准确率明显低于基线；加入 SE 后准确率略有改善；GroupNorm + GELU 模型的损失下降最慢，8 轮结束时仍未充分收敛，"
     "因此准确率最低。这说明归一化和激活函数的替换并不是“越新越好”，需要与训练轮次和优化设置匹配。")
figure(os.path.join(RES, "curves.png"), 15.0, "图 3  四个模型的训练损失与测试准确率曲线")

heading("5.3  混淆矩阵与类别分析", 2)
para("最终模型在测试集上的归一化混淆矩阵如图 4 所示。对角线越深表示该类识别越准确。可以看到，汽车、船、卡车等类别辨识度较高；"
     "猫和狗、鸟和鹿等类别之间存在一定混淆，原因是 32×32 分辨率下这些类别的纹理和轮廓较为相似。"
     "这也说明，轻量化结构降低了模型容量，细粒度类别仍需要更高分辨率、更强数据增强或更长的训练。")
figure(os.path.join(RES, "confusion.png"), 10.5, "图 4  最终模型在 CIFAR-10 测试集上的归一化混淆矩阵")

heading("5.4  消融分析", 2)
para("从表 3 可以分解出三种结构修改的贡献：")
bullet(f"深度可分离卷积：参数量降低 {(1-m['ds']['params_m']/m['base']['params_m'])*100:.1f}%，MACs 降低 "
       f"{(1-m['ds']['macs_m']/m['base']['macs_m'])*100:.1f}%，准确率变化 {(m['ds']['test_acc']-m['base']['test_acc'])*100:+.2f} 个百分点；")
bullet(f"SE 注意力：在深度可分离模型上准确率变化 {(m['ds_se']['test_acc']-m['ds']['test_acc'])*100:+.2f} 个百分点，"
       f"参数量仅增加 {m['ds_se']['params_m']-m['ds']['params_m']:.3f} M；")
bullet(f"GroupNorm + GELU：在 DS+SE 上准确率变化 {(m['final']['test_acc']-m['ds_se']['test_acc'])*100:+.2f} 个百分点，参数量基本不变。")
para("需要说明的是，CIFAR-10 单次训练的准确率存在一定随机波动，上述差值只能反映趋势；更严格的结论应多次重复训练并报告均值和方差。"
     "此外，本实验只训练 8 轮，基线并未完全收敛，因此绝对准确率低于文献中长时间训练的结果，但四个模型的比较是在相同条件下进行的。")

heading("5.5  场景应用", 2)
para("改进模型的核心优势是“参数量和计算量大幅降低，同时保持可接受的准确率”，适合部署在算力和存储受限的边缘设备上。"
     "例如，在智能交通场景中，可以将该模型部署到路口摄像头或车载终端，对车辆、飞机、船等目标进行粗分类，为后续的细粒度识别和目标跟踪提供候选区域；"
     "在移动端相册应用中，可用于快速场景/物体分类；在工业质检中，可作为轻量预筛选模型，把疑似缺陷图像交给更大的模型复核。")
para("以智能交通为例，深度可分离卷积降低了模型对内存带宽和算力的需求，SE 注意力帮助模型关注车辆轮廓等关键通道，"
     "GroupNorm 不依赖大 batch，适合边缘端小批量推理。若需要部署到嵌入式设备，还可以进一步使用量化、剪枝和 TensorRT/ONNX Runtime 加速。")

# 6
heading("6  总结", 1)
para(f"本作业在 CIFAR-10 上实现了一个 VGG 式经典 CNN，并从深度可分离卷积、SE 注意力、GroupNorm/GELU 三个方向进行了结构改进。"
     f"实验结果表明：基线模型参数量 {m['base']['params_m']:.3f} M、测试准确率 {P(m['base']['test_acc'])}；"
     f"深度可分离模型把参数量降到 {m['ds']['params_m']:.3f} M，准确率 {P(m['ds']['test_acc'])}；"
     f"加入 SE 后准确率 {P(m['ds_se']['test_acc'])}；GroupNorm/GELU 组合在 8 轮训练下仅达到 {P(m['final']['test_acc'])}，"
     "说明该组合需要更长的训练或更细致的学习率调整。")
para("综合精度和复杂度，DS+SE 是本实验推荐的轻量方案：参数量仅为基线的 " +
     f"{m['ds_se']['params_m']/m['base']['params_m']*100:.1f}%，MACs 为基线的 "
     f"{m['ds_se']['macs_m']/m['base']['macs_m']*100:.1f}%，准确率 {P(m['ds_se']['test_acc'])}。"
     "通过本作业，理解了标准卷积与深度可分离卷积在计算方式上的差异，掌握了 SE 注意力、GroupNorm 和 GELU 的实现方法，"
     "也体会到了模型设计中精度、参数量、计算量和训练预算之间的权衡。")

# 参考文献
heading("参考文献", 1)
refs = [
    "[1] SIMONYAN K, ZISSERMAN A. Very deep convolutional networks for large-scale image recognition[C]//ICLR. 2015.",
    "[2] HOWARD A G, ZHU M, CHEN B, et al. MobileNets: Efficient convolutional neural networks for mobile vision applications[J]. arXiv:1704.04861, 2017.",
    "[3] HU J, SHEN L, SUN G. Squeeze-and-excitation networks[C]//CVPR. 2018: 7132-7141.",
    "[4] WU Y, HE K. Group normalization[C]//ECCV. 2018: 3-19.",
    "[5] HENDRYCKS D, GIMPEL K. Gaussian error linear units (GELUs)[J]. arXiv:1606.08415, 2016.",
    "[6] KRIZHEVSKY A, HINTON G. Learning multiple layers of features from tiny images[R]. University of Toronto, 2009.",
]
for ref in refs:
    p = para(indent=False, after=4, line=1.25, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    p.paragraph_format.left_indent = Cm(0.75)
    p.paragraph_format.first_line_indent = Cm(-0.75)
    run(p, ref, 10.5)

# 附录
heading("附录 A  代码与运行说明", 1)
para("代码、数据集和结果均保存在 cnn_hw 目录下，目录结构如下：")
code_block("""cnn_hw/
├─ code/
│  ├─ train_cnn.py        # 四个模型的训练与评价
│  └─ make_figures.py     # 曲线、效率图、混淆矩阵
├─ data/                  # CIFAR-10（不提交 Git）
├─ results/               # 指标 JSON、日志、图表、权重
├─ README.md
├─ requirements.txt
└─ 课内大作业报告_基于结构改进的轻量CNN图像分类.docx""", "目录结构")
para("运行顺序如下：")
code_block("""pip install -r requirements.txt
python code/train_cnn.py --model base --epochs 8 --batch 256 --train_size 25000
python code/train_cnn.py --model ds --epochs 8 --batch 256 --train_size 25000
python code/train_cnn.py --model ds_se --epochs 8 --batch 256 --train_size 25000
python code/train_cnn.py --model final --epochs 8 --batch 256 --train_size 25000
python code/make_figures.py""", "运行命令")
para("训练脚本固定随机种子 42，四个模型使用相同的训练/测试划分；每个模型的最优权重、指标 JSON 和训练日志保存在 results 目录。"
     "报告中的准确率、参数量和 MACs 均由脚本输出并写入 JSON，可直接复核。")
para("代码仓库：本作业已初始化本地 Git 仓库并提交全部源码、README 和运行说明；远程仓库地址（GitHub/Gitee）见提交时补充。")

doc.save(OUT)
print("saved:", OUT)
