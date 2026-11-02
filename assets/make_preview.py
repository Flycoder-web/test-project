#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 README 渲染成自包含的 HTML 预览：所有本地图片内嵌为 data URI。

用途：本地编辑器/预览器不解析相对路径或挡 file:// 时，直接打开生成的 HTML
即可看到全部图片（gif / svg / jpg 都能显示）。README 源文件不做任何改动。
"""
import base64
import os
import re

import markdown

WORKDOC = "/root/workdoc"
REPO = "/root/grape-dev-repo"

MIME = {".gif": "image/gif", ".png": "image/png", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".webp": "image/webp"}

CSS = """
:root { color-scheme: light; }
body { max-width: 980px; margin: 0 auto; padding: 32px 24px 80px;
       font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC",
             "PingFang SC", "Microsoft YaHei", sans-serif;
       color: #1f2328; background: #fff; }
h1, h2, h3 { line-height: 1.25; margin-top: 1.6em; padding-bottom: .3em; }
h1 { font-size: 2em; border-bottom: 1px solid #d8dee4; }
h2 { font-size: 1.5em; border-bottom: 1px solid #d8dee4; }
h3 { font-size: 1.2em; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
img { max-width: 100%; height: auto; }
table { border-collapse: collapse; margin: 1em 0; display: block; overflow-x: auto; }
th, td { border: 1px solid #d0d7de; padding: 6px 13px; }
th { background: #f6f8fa; }
tr:nth-child(2n) td { background: #f6f8fa; }
code { background: #f6f8fa; padding: .2em .4em; border-radius: 6px;
       font: 85%/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
pre { background: #f6f8fa; padding: 14px 16px; border-radius: 8px; overflow-x: auto; }
pre code { background: none; padding: 0; }
blockquote { margin: 1em 0; padding: 0 1em; color: #59636e; border-left: .25em solid #d0d7de; }
hr { border: 0; border-top: 1px solid #d8dee4; margin: 2em 0; }
details { margin: 1em 0; }
summary { cursor: pointer; font-weight: 600; }
.banner { background: #fff8c5; border: 1px solid #d4a72c; border-radius: 8px;
          padding: 10px 14px; font-size: 14px; margin-bottom: 24px; }
"""


def inline_images(html: str) -> tuple[str, list[str]]:
    """把 <img src="本地路径"> 换成 data URI，返回 (html, 未找到的路径)。"""
    missing = []

    def repl(m):
        prefix, src, suffix = m.group(1), m.group(2), m.group(3)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        for base in (WORKDOC, REPO):
            path = os.path.join(base, src)
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                mime = MIME.get(os.path.splitext(path)[1].lower(), "application/octet-stream")
                return f'{prefix}data:{mime};base64,{b64}{suffix}'
        missing.append(src)
        return m.group(0)

    html = re.sub(r'(\bsrc=")([^"]+)(")', repl, html)
    return html, missing


def build(src_md: str, out_html: str, title: str):
    text = open(src_md, encoding="utf-8").read()
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html", "toc"],
        output_format="html5",
    )
    body, missing = inline_images(body)
    html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}（本地预览）</title>
<style>{CSS}</style></head><body>
<div class="banner">本地预览：所有图片已内嵌（data URI），与发布用的 Markdown 源文件内容一致。
源文件：<code>{os.path.basename(src_md)}</code></div>
{body}
</body></html>
"""
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{os.path.basename(out_html)}: {len(html)/1024:.0f} KB"
          + (f" | 未找到的图片: {missing}" if missing else " | 全部图片已内嵌"))


if __name__ == "__main__":
    build(f"{WORKDOC}/readme-zh.md", f"{WORKDOC}/readme-zh.preview.html", "Grape README 中文")
    build(f"{WORKDOC}/readme.md", f"{WORKDOC}/readme.preview.html", "Grape README (English)")
