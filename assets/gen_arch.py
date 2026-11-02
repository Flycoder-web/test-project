#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 Grape 五层架构图（SVG + PNG，中英各一份）。

布局即 README「架构」一节的 Mermaid 流程图：
入口层 → 编排层 → 引擎层（可插拔）→ 隔离层 → 交付层
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- 布局常量（逻辑像素） ----------
M = 28
TITLE_H = 56
COL_W = 250
GAP = 46
N_COLS = 5
CHIP_H = 34
CHIP_GAP = 8
HEADER_H = 40
PAD = 14
CHIPS_MAX = 6

CONTAINER_H = HEADER_H + CHIPS_MAX * (CHIP_H + CHIP_GAP) - CHIP_GAP + PAD * 2
CONTENT_TOP = M + TITLE_H + 16
W = M * 2 + N_COLS * COL_W + (N_COLS - 1) * GAP
H = CONTENT_TOP + CONTAINER_H + M + 40

# ---------- 配色 ----------
BG = "#ffffff"
BORDER = "#d0d7de"
CHIP_BG = "#ffffff"
CHIP_STROKE = "#d0d7de"
TEXT = "#24292f"
MUTED = "#59636e"
ARROW = "#8c959f"
TITLE_C = "#1f2328"

LAYERS = [
    {
        "zh": "入口层", "en": "Ingress",
        "job_zh": "接收事件与人的指令", "job_en": "events & human commands",
        "accent": "#0969da", "tint": "#ddf4ff",
        "chips_zh": ["GitCode Webhook", "GitHub Webhook", "飞书 WebSocket 长连接", "WebUI / Grape CLI"],
        "chips_en": ["GitCode Webhook", "GitHub Webhook", "Feishu WebSocket", "WebUI / Grape CLI"],
    },
    {
        "zh": "编排层", "en": "Orchestration",
        "job_zh": "决定谁在什么顺序做什么", "job_en": "who does what, in which order",
        "accent": "#8250df", "tint": "#fbefff",
        "chips_zh": ["Agent 定义", "Agent × Skill 映射", "A2A 交接", "任务中心"],
        "chips_en": ["Agent definitions", "Agent × Skill mapping", "A2A handoff", "Task center"],
    },
    {
        "zh": "引擎层（可插拔）", "en": "Engines (pluggable)",
        "job_zh": "实际执行编码工作", "job_en": "does the actual coding work",
        "accent": "#1a7f37", "tint": "#dafbe1",
        "chips_zh": ["opencode", "codearts", "hermes", "codex", "dsh", "hwcloud"],
        "chips_en": ["opencode", "codearts", "hermes", "codex", "dsh", "hwcloud"],
    },
    {
        "zh": "隔离层", "en": "Isolation",
        "job_zh": "让执行受控且可恢复", "job_en": "bounded, recoverable execution",
        "accent": "#bc4c00", "tint": "#fff1e5",
        "chips_zh": ["Worker 节点", "按 Issue 划分工作区", "bwrap 沙箱（可选）"],
        "chips_en": ["Worker node", "workspace per Issue", "optional bwrap sandbox"],
    },
    {
        "zh": "交付层", "en": "Delivery",
        "job_zh": "把结果交付出去", "job_en": "ships the result",
        "accent": "#cf222e", "tint": "#ffebe9",
        "chips_zh": ["构建", "部署", "监控", "发布管理"],
        "chips_en": ["Build", "Deploy", "Observe", "Release"],
    },
]

SUB_ZH = "多智能体 DevOps 平台 · 五层解耦，逐层可替换"
SUB_EN = "Multi-agent DevOps platform · five decoupled, swappable layers"
TITLE_ZH = "Grape 架构"
TITLE_EN = "Grape Architecture"
FOOT_ZH = "每个 Issue 在工作区内由一个引擎执行；引擎通过 register_backend() 挂载，场景决定 Agent × Skill 的组合"
FOOT_EN = "Each Issue runs in its own workspace via one engine; engines plug in through register_backend(); scenes define the Agent × Skill combination"

# 运行实例 favicon 抠出的葡萄图标（去文字、透明底）
ICON_PATH = os.path.join(OUT, "grape-icon.png")
ICON_H = 30
TITLE_X = M + ICON_H + 8


def col_x(i):
    return M + i * (COL_W + GAP)


def chips_geometry(n):
    """返回第一个 chip 的 y 偏移（在容器内垂直居中）。"""
    total = n * CHIP_H + (n - 1) * CHIP_GAP
    inner = CONTAINER_H - HEADER_H - PAD * 2
    return HEADER_H + PAD + max(0, (inner - total) / 2)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(lang):
    zh = lang == "zh"
    font = "WenQuanYi Zen Hei, Noto Sans CJK SC, PingFang SC, Microsoft YaHei, sans-serif" if zh \
        else "Segoe UI, Helvetica, Arial, sans-serif"
    title = TITLE_ZH if zh else TITLE_EN
    sub = SUB_ZH if zh else SUB_EN
    foot = FOOT_ZH if zh else FOOT_EN
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
             f'font-family="{font}" role="img" aria-label="{esc(title)}">')
    p.append(f'  <rect width="{W}" height="{H}" rx="14" fill="{BG}"/>')
    p.append(f'  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="{BORDER}"/>')
    if os.path.exists(ICON_PATH):
        import base64
        import io as _io
        # SVG 内嵌用小尺寸（头部显示仅 30px 高），避免 base64 撑大文件
        _ic = Image.open(ICON_PATH).convert("RGBA")
        _ic = _ic.resize((max(1, int(_ic.width * 96 / _ic.height)), 96), Image.LANCZOS)
        _buf = _io.BytesIO()
        _ic.save(_buf, format="PNG", optimize=True)
        _b64 = base64.b64encode(_buf.getvalue()).decode()
        p.append(f'  <image x="{M}" y="{M+4}" height="{ICON_H}" href="data:image/png;base64,{_b64}"/>')
    p.append(f'  <text x="{TITLE_X}" y="{M+30}" font-size="26" font-weight="700" fill="{TITLE_C}">{esc(title)}</text>')
    p.append(f'  <text x="{TITLE_X}" y="{M+52}" font-size="14" fill="{MUTED}">{esc(sub)}</text>')

    for i, L in enumerate(LAYERS):
        x = col_x(i)
        y = CONTENT_TOP
        chips = L["chips_zh"] if zh else L["chips_en"]
        name = L["zh"] if zh else L["en"]
        job = L["job_zh"] if zh else L["job_en"]
        p.append(f'  <rect x="{x}" y="{y}" width="{COL_W}" height="{CONTAINER_H}" rx="12" '
                 f'fill="{L["tint"]}" stroke="{L["accent"]}" stroke-opacity="0.35"/>')
        p.append(f'  <text x="{x+PAD+2}" y="{y+26}" font-size="16" font-weight="700" fill="{L["accent"]}">{esc(name)}</text>')
        p.append(f'  <text x="{x+PAD+2}" y="{y+42}" font-size="11" fill="{MUTED}">{esc(job)}</text>')
        cw = COL_W - PAD * 2
        oy = chips_geometry(len(chips))
        for k, c in enumerate(chips):
            cy = y + oy + k * (CHIP_H + CHIP_GAP)
            p.append(f'  <rect x="{x+PAD}" y="{cy}" width="{cw}" height="{CHIP_H}" rx="8" '
                     f'fill="{CHIP_BG}" stroke="{CHIP_STROKE}"/>')
            p.append(f'  <text x="{x+COL_W/2}" y="{cy+CHIP_H/2+5}" font-size="13" fill="{TEXT}" '
                     f'text-anchor="middle">{esc(c)}</text>')
        if i < N_COLS - 1:
            ax0 = x + COL_W + 8
            ax1 = col_x(i + 1) - 8
            ay = y + CONTAINER_H / 2
            p.append(f'  <line x1="{ax0}" y1="{ay}" x2="{ax1-7}" y2="{ay}" stroke="{ARROW}" '
                     f'stroke-width="2" stroke-linecap="round"/>')
            p.append(f'  <path d="M{ax1-9},{ay-5} L{ax1},{ay} L{ax1-9},{ay+5} Z" fill="{ARROW}"/>')
    p.append(f'  <text x="{M}" y="{H-M-6}" font-size="12" fill="{MUTED}">{esc(foot)}</text>')
    p.append('</svg>')
    return "\n".join(p) + "\n"


def load_fonts(zh, scale):
    if zh:
        path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
        return (ImageFont.truetype(path, int(26 * scale)),
                ImageFont.truetype(path, int(15 * scale)),
                ImageFont.truetype(path, int(16 * scale)),
                ImageFont.truetype(path, int(12 * scale)),
                ImageFont.truetype(path, int(13 * scale)),
                ImageFont.truetype(path, int(11 * scale)),
                ImageFont.truetype(path, int(12 * scale)))
    base = "/usr/share/fonts/dejavu/DejaVuSans.ttf"
    bold = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"
    return (ImageFont.truetype(bold, int(26 * scale)),
            ImageFont.truetype(base, int(15 * scale)),
            ImageFont.truetype(bold, int(16 * scale)),
            ImageFont.truetype(base, int(12 * scale)),
            ImageFont.truetype(base, int(13 * scale)),
            ImageFont.truetype(base, int(11 * scale)),
            ImageFont.truetype(base, int(12 * scale)))


def build_png(lang, scale=3):
    zh = lang == "zh"
    f_title, f_sub, f_head, f_job, f_chip, f_foot, _ = load_fonts(zh, scale)
    S = lambda v: int(round(v * scale))
    img = Image.new("RGB", (S(W), S(H)), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, S(W) - 1, S(H) - 1], radius=S(14), outline=BORDER, width=max(1, int(scale)))

    title = TITLE_ZH if zh else TITLE_EN
    sub = SUB_ZH if zh else SUB_EN
    foot = FOOT_ZH if zh else FOOT_EN
    if os.path.exists(ICON_PATH):
        ic = Image.open(ICON_PATH).convert("RGBA")
        ih = int(ICON_H * scale)
        ic = ic.resize((max(1, int(ic.width * ih / ic.height)), ih), Image.LANCZOS)
        img.paste(ic, (S(M), S(M + 6)), ic)
    d.text((S(TITLE_X), S(M + 8)), title, font=f_title, fill=TITLE_C)
    d.text((S(TITLE_X), S(M + 38)), sub, font=f_sub, fill=MUTED)

    for i, L in enumerate(LAYERS):
        x, y = col_x(i), CONTENT_TOP
        chips = L["chips_zh"] if zh else L["chips_en"]
        name = L["zh"] if zh else L["en"]
        job = L["job_zh"] if zh else L["job_en"]
        d.rounded_rectangle([S(x), S(y), S(x + COL_W), S(y + CONTAINER_H)], radius=S(12),
                            fill=L["tint"], outline=L["accent"], width=max(1, int(scale * 0.8)))
        d.text((S(x + PAD + 2), S(y + 12)), name, font=f_head, fill=L["accent"])
        d.text((S(x + PAD + 2), S(y + 34)), job, font=f_job, fill=MUTED)
        cw = COL_W - PAD * 2
        oy = chips_geometry(len(chips))
        for k, c in enumerate(chips):
            cy = y + oy + k * (CHIP_H + CHIP_GAP)
            d.rounded_rectangle([S(x + PAD), S(cy), S(x + PAD + cw), S(cy + CHIP_H)], radius=S(8),
                                fill=CHIP_BG, outline=CHIP_STROKE, width=max(1, int(scale * 0.8)))
            tw = d.textlength(c, font=f_chip)
            d.text((S(x + COL_W / 2) - tw / 2, S(cy + 8)), c, font=f_chip, fill=TEXT)
        if i < N_COLS - 1:
            ax0, ax1 = x + COL_W + 8, col_x(i + 1) - 8
            ay = y + CONTAINER_H / 2
            d.line([S(ax0), S(ay), S(ax1 - 9), S(ay)], fill=ARROW, width=max(1, int(2 * scale)))
            d.polygon([(S(ax1 - 9), S(ay - 5)), (S(ax1), S(ay)), (S(ax1 - 9), S(ay + 5))], fill=ARROW)
    d.text((S(M), S(H - M - 22)), foot, font=f_foot, fill=MUTED)
    return img


if __name__ == "__main__":
    for lang, suffix in (("en", ""), ("zh", "-zh")):
        svg_path = os.path.join(OUT, f"architecture{suffix}.svg")
        png_path = os.path.join(OUT, f"architecture{suffix}.png")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(build_svg(lang))
        build_png(lang, 3).save(png_path)
        print("wrote", svg_path, os.path.getsize(svg_path), "bytes")
        print("wrote", png_path, os.path.getsize(png_path), "bytes")
