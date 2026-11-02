#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「Issue 在 Agent 间自动流转」流水线动画（GIF）。

运动语言参考 grape 官网 workflow 段：
  - 5 个节点，各带彩色圆点 + 名称 + 职责
  - 节点间连线有一道渐变光带流过（flow 关键帧）
  - 当前节点下方 3 条活动文本依次浮起并保留（wfBubble 关键帧）
  - 段间交接标记 A2A；QA 不通过时有一条回流边退回 Coding
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------- 画布与布局（逻辑像素，内部 2 倍超采样后缩放） ----------------
W, H = 1320, 292
S2 = 2  # 超采样倍率

MARGIN = 36
NODE_W, NODE_H = 152, 78
NODE_TOP = 62
AREA_ACT = 168          # 活动文本起始 y
AREA_FOOT = 258         # 底部说明行 y

# ---------------- 主题 ----------------
THEMES = {
    "light": dict(
        bg="#ffffff", panel="#ffffff", border="#d0d7de", text="#1f2328",
        muted="#59636e", line="#d0d7de", chip="#f6f8fa", chip_bd="#d0d7de",
        done_line="#b7bfc7", foot="#59636e", status="#59636e", reject="#cf222e",
    ),
    "dark": dict(
        bg="#0c0c14", panel="#15151f", border="#2a2a3a", text="#ececf5",
        muted="#9a9aad", line="#2a2a3a", chip="#1b1b28", chip_bd="#2f2f42",
        done_line="#3a3a4d", foot="#9a9aad", status="#9a9aad", reject="#ff6b6b",
    ),
}

NODES = [
    dict(zh="VOD 开发者之声", en="VOD", desc_zh="收集反馈", desc_en="Collect feedback",
         color="#ec4899", tint="#fde8f4",
         act_zh=["收到反馈", "聚类洞察", "创建可开发 Issue"],
         act_en=["feedback received", "clustering themes", "issue created"]),
    dict(zh="Issue 任务编排", en="Issue", desc_zh="分流与指派", desc_en="Triage & assign",
         color="#f59e0b", tint="#fef4e3",
         act_zh=["分类打标", "指派负责人", "触发 A2A 交接"],
         act_en=["auto-labeled", "assigned", "A2A triggered"]),
    dict(zh="Coding 代码实现", en="Coding", desc_zh="实现与自审", desc_en="Implement & PR",
         color="#3b82f6", tint="#e8f1fe",
         act_zh=["编写代码", "自我评审", "开启 Pull Request"],
         act_en=["writing code", "self-review", "PR opened"]),
    dict(zh="QA 质量守门", en="QA", desc_zh="评审与测试", desc_en="Review & test",
         color="#10b981", tint="#e6f7f1",
         act_zh=["代码评审", "运行测试", "安全扫描"],
         act_en=["code review", "running tests", "security scan"]),
    dict(zh="SRE 部署运维", en="SRE", desc_zh="构建与上线", desc_en="Build & deploy",
         color="#06b6d4", tint="#e2f7fb",
         act_zh=["构建镜像", "部署上线", "结果回写 Issue"],
         act_en=["building image", "deploying", "live in prod"]),
]

TXT = {
    "zh": dict(
        title="Grape 流水线 · Issue 在 Agent 之间自动流转",
        status="第 {i}/5 段：{name}",
        foot="段间只传 A2A 事件，不共享上下文；每段是一个 Agent，挂一个技能",
        reject="QA 驳回 → 自动退回 Coding 重做",
        done="上线结果回写 Issue —— 全程无人工转派",
        token="Issue #143",
    ),
    "en": dict(
        title="Grape pipeline · issues flow through agents on their own",
        status="stage {i}/5: {name}",
        foot="Each stage is one agent with one skill; hand-offs are A2A events, no shared context",
        reject="QA rejects → routed back to Coding automatically",
        done="Deploy result written back to the Issue — no manual handoff at all",
        token="Issue #143",
    ),
}

FONT_CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
FONT_R = "/usr/share/fonts/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"


def fonts(zh, s):
    def f(path, size):
        return ImageFont.truetype(path, int(size * s))
    if zh:
        return dict(title=f(FONT_CJK, 15), name=f(FONT_CJK, 14), desc=f(FONT_CJK, 11),
                    act=f(FONT_CJK, 11), foot=f(FONT_CJK, 11), token=f(FONT_CJK, 11),
                    status=f(FONT_CJK, 11))
    return dict(title=f(FONT_B, 14), name=f(FONT_B, 13), desc=f(FONT_R, 11),
                act=f(FONT_R, 11), foot=f(FONT_R, 11), token=f(FONT_R, 11),
                status=f(FONT_R, 11))


def node_cx(i):
    """第 i 个节点中心 x（整体水平居中，等间距）。"""
    span = W - 2 * MARGIN
    step = span / len(NODES)
    return MARGIN + step * (i + 0.5)


def rr(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_frame(stage, t_stage, beat, theme, lang, size_kw):
    """stage: 当前活动节点索引 0..4（5=全部完成）；t_stage: 本段进度 0..1；beat: 帧类型
    beat: 'travel' | 'work' | 'reject' | 'done'"""
    th = THEMES[theme]
    T = TXT[lang]
    s = S2
    img = Image.new("RGB", (W * s, H * s), th["bg"])
    d = ImageDraw.Draw(img)
    F = fonts(lang == "zh", s)

    def X(v):
        return v * s

    def put(xy, text, font, fill, anchor="la"):
        d.text((X(xy[0]), X(xy[1])), text, font=font, fill=fill, anchor=anchor)

    # 外框
    rr(d, [X(1), X(1), X(W - 1), X(H - 1)], X(10), outline=th["border"], width=max(1, s // 2))

    # 标题 + 状态
    put((MARGIN, 18), T["title"], F["title"], th["text"])
    if beat == "done":
        status = T["done"]
        st_color = NODES[-1]["color"]
    elif stage < len(NODES):
        status = T["status"].format(i=stage + 1, name=NODES[stage]["zh" if lang == "zh" else "en"])
        st_color = NODES[stage]["color"]
    else:
        status = ""
        st_color = th["status"]
    if status:
        put((W - MARGIN, 20), status, F["status"], st_color, anchor="ra")

    # 节点
    for i, n in enumerate(NODES):
        cx = node_cx(i)
        x0, y0 = cx - NODE_W / 2, NODE_TOP
        x1, y1 = cx + NODE_W / 2, NODE_TOP + NODE_H
        active = (i == stage and beat in ("travel", "work"))
        done = (i < stage) or (beat == "done") or (stage == len(NODES))
        fill = n["tint"] if (theme == "light" and (active or done)) else th["panel"]
        if theme == "dark" and (active or done):
            fill = mix(th["panel"], n["color"], 0.12)
        border = n["color"] if (active or done) else th["border"]
        rr(d, [X(x0), X(y0), X(x1), X(y1)], X(10), fill=fill, outline=border,
           width=max(1, s // 2 if not active else s))
        # 圆点
        dr = 5
        dcx, dcy = cx, y0 + 16
        if active:
            d.ellipse([X(dcx - dr - 3), X(dcy - dr - 3), X(dcx + dr + 3), X(dcy + dr + 3)],
                      outline=n["color"], width=max(1, s // 2))
        if done:
            d.ellipse([X(dcx - dr), X(dcy - dr), X(dcx + dr), X(dcy + dr)], fill=n["color"])
        else:
            d.ellipse([X(dcx - dr), X(dcy - dr), X(dcx + dr), X(dcy + dr)],
                      fill=n["color"] if active else th["bg"], outline=n["color"],
                      width=max(1, s // 2))
        put((cx, y0 + 26), n["zh" if lang == "zh" else "en"], F["name"], th["text"], anchor="ma")
        put((cx, y0 + 48), n["desc_zh" if lang == "zh" else "desc_en"], F["desc"], th["muted"], anchor="ma")

    # 连线 + 光带 + 流动的 Issue 令牌
    for i in range(len(NODES) - 1):
        xa = node_cx(i) + NODE_W / 2 + 6
        xb = node_cx(i + 1) - NODE_W / 2 - 6
        y = NODE_TOP + NODE_H / 2
        passed = (i < stage) or (stage == len(NODES)) or beat == "done"
        color = NODES[i + 1]["color"] if passed else th["line"]
        alpha_t = 1.0
        if i == stage and beat in ("travel", "work"):
            alpha_t = 0.35 + 0.65 * min(1.0, t_stage * 2.2)
        d.line([X(xa), X(y), X(xb), X(y)], fill=mix(th["line"], color, alpha_t),
               width=max(1, s * (1 if not passed else 2) // 2 + 1))
        # 光带
        if i == stage and beat == "travel":
            pos = t_stage
            seg = 26
            x0p = xa + (xb - xa) * max(0.0, pos - 0.25)
            x1p = xa + (xb - xa) * min(1.0, pos + 0.25)
            if x1p > x0p:
                d.line([X(x0p), X(y), X(x1p), X(y)], fill=NODES[i + 1]["color"], width=max(1, s * 2))
        # 令牌
        if i == stage and beat == "travel":
            tx = xa + (xb - xa) * t_stage
            tw, thh = 82, 22
            rr(d, [X(tx - tw / 2), X(y - thh / 2), X(tx + tw / 2), X(y + thh / 2)], X(11),
               fill=th["chip"], outline=NODES[i + 1]["color"], width=max(1, s // 2))
            put((tx, y - 6), T["token"], F["token"], th["text"], anchor="ma")

    # 当前节点的活动文本：逐条浮起并保留
    if stage < len(NODES):
        n = NODES[stage]
        acts = n["act_zh"] if lang == "zh" else n["act_en"]
        cx = node_cx(stage)
        shown = 3
        if beat == "travel":
            shown = 0
        elif beat == "work":
            shown = min(3, max(1, int(t_stage * 3.4) + 1))
        for k in range(min(shown, len(acts))):
            yk = AREA_ACT + k * 22
            appear = 1.0
            if beat == "work":
                seg = 1 / 3.4
                appear = min(1.0, max(0.0, (t_stage - k * seg) / (seg * 0.9)))
            if appear <= 0:
                continue
            fill = mix(th["bg"], n["color"], appear)
            rr(d, [X(cx - 78), X(yk - 3), X(cx + 78), X(yk + 17)], X(9), fill=th["chip"],
               outline=mix(th["chip_bd"], n["color"], appear), width=max(1, s // 2))
            put((cx, yk + 1), acts[k], F["act"], fill, anchor="ma")

    # 底部：A2A 说明 / 回流边 / 完成
    if beat == "reject":
        put((MARGIN, AREA_FOOT), T["reject"], F["foot"], th["reject"])
        # 回流箭头 QA → Coding
        xa, xb = node_cx(3), node_cx(2)
        y = NODE_TOP + NODE_H + 6
        d.line([X(xa), X(y), X(xa), X(y + 16), X(xb), X(y + 16), X(xb), X(y + 6)],
               fill=th["reject"], width=max(1, s), joint="curve")
        d.polygon([(X(xb - 5), X(y + 6)), (X(xb + 5), X(y + 6)), (X(xb), X(y - 1))], fill=th["reject"])
    else:
        put((MARGIN, AREA_FOOT), T["foot"], F["foot"], th["foot"])
    if beat == "done":
        put((W - MARGIN, AREA_FOOT), T["done"], F["foot"], NODES[-1]["color"], anchor="ra")
    return img.resize((W, H), Image.LANCZOS)


def render_frames(theme, lang, stage_s=1.4, fps=15, scale=1.0):
    """渲染全部帧（RGB），并返回 (frames, 每帧时长 ms)。"""
    global W, H, MARGIN, NODE_W, NODE_H, NODE_TOP, AREA_ACT, AREA_FOOT
    if scale != 1.0:
        W = int(W * scale); H = int(H * scale)
        MARGIN = int(MARGIN * scale); NODE_W = int(NODE_W * scale); NODE_H = int(NODE_H * scale)
        NODE_TOP = int(NODE_TOP * scale); AREA_ACT = int(AREA_ACT * scale); AREA_FOOT = int(AREA_FOOT * scale)
    ms = int(1000 / fps)
    frames = []
    travel = max(3, int(stage_s * 0.45 * fps))
    work = max(3, int(stage_s * 0.55 * fps))
    for stage in range(len(NODES)):
        for k in range(travel):
            frames.append(draw_frame(stage, k / travel, "travel", theme, lang, None))
        for k in range(work):
            frames.append(draw_frame(stage, k / work, "work", theme, lang, None))
    for _ in range(max(3, int(1.2 * fps))):      # 质量闭环回流
        frames.append(draw_frame(4, 0, "reject", theme, lang, None))
    for _ in range(max(3, int(1.0 * fps))):      # 完成态
        frames.append(draw_frame(len(NODES), 0, "done", theme, lang, None))
    return frames, ms


def encode(frames, ms, out_base, scale=1.0):
    """用 ffmpeg 编码 GIF（palettegen/paletteuse，带帧间优化）+ mp4 + webm。"""
    import shutil
    import subprocess
    tmp = os.path.join(OUT, ".frames_tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    for idx, f in enumerate(frames):
        if scale != 1.0:
            f = f.resize((int(f.width * scale), int(f.height * scale)), Image.LANCZOS)
        f.save(os.path.join(tmp, "f%04d.png" % idx))
    fps = round(1000 / ms, 4)
    tgt = (int(frames[0].width * scale), int(frames[0].height * scale))
    even = (tgt[0] - tgt[0] % 2, tgt[1] - tgt[1] % 2)
    inp = ["-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png")]

    gif = out_base + ".gif"
    vf = ("fps=%s,scale=%d:%d:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];"
          "[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" % (fps, tgt[0], tgt[1]))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inp + ["-vf", vf, "-loop", "0", gif], check=True)
    webm = out_base + ".webm"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inp +
                   ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34", "-pix_fmt", "yuv420p",
                    "-vf", "scale=%d:%d:flags=lanczos" % even, webm], check=True)
    mp4 = out_base + ".mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + inp +
                   ["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-vf", "scale=%d:%d:flags=lanczos" % even, mp4], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return {os.path.basename(p): os.path.getsize(p) for p in (gif, webm, mp4)}


if __name__ == "__main__":
    for theme in ("light", "dark"):
        for lang, suf in (("en", ""), ("zh", "-zh")):
            tag = f"pipeline-flow{suf}{'' if theme == 'light' else '-dark'}"
            frames, ms = render_frames(theme, lang)
            sizes = encode(frames, ms, os.path.join(OUT, tag))
            print(tag, len(frames), "frames,", {k: f"{v/1024:.0f}KB" for k, v in sizes.items()})
