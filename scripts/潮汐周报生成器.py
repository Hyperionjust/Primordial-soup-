#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
潮汐周报生成器：把 _氨基酸库/潮汐周报/潮汐-YYYY-MM-DD.md 渲染成一页静态 HTML。

用法：
    py 潮汐周报生成器.py <周报md路径> [输出html路径]
    默认输出＝同目录同名 .html。

设计约束（2026-08-09 定）：
1. 全静态、零 JavaScript——周报是定稿文档，渲染全部在 Python 侧完成；无外部资源，
   图形一律内联手写 SVG。
2. 内容无损优先于美观：已知结构美化、未知结构原样成段，绝不丢内容。生成后内置对账
   （html 去标签文本 ⊇ md 每一行文本，均折叠空白），结果打进页脚并回报 stdout；
   有缺失时 stdout 报明细并以退出码 3 结束（文件仍会写出，便于比对）。
3. 视觉分区（防止 AI 判断混进数据的视觉权威里）：
   数据区（对账／清欠／尾注）潮汐青细边，区头「台账事实」；
   提议区（簇检测／提议／回溯碰撞提案／打包提议）闪电色细边 + 「提案 · 待裁定」徽章，
   区头「AI 预填，裁定在用户」。未知版块名归中性样式，不带徽章、不进任何一区。
4. 仅用 Python 3 标准库。

排版取舍：md 的每一非空行渲染成独立段落（周报是一行一段的写法），因此不做软换行合并；
拆行渲染既可读又保证逐行可对账。
"""

import sys
import os
import re
import datetime
from html import escape as _html_escape
from html.parser import HTMLParser

# R6：Windows 下重定向 stdout/stderr 时强制 UTF-8，避免中文以系统本地编码（GBK）落盘；
# 对账结论以 UTF-8 落盘可读。读文件仍按 utf-8-sig，解析/对账逻辑不变。
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

GEN_PATH_LABEL = "_氨基酸库/潮汐周报生成器.py"

# ============================== 分区规则 ==============================
ZONE_DATA, ZONE_PROP, ZONE_NEUTRAL = "data", "prop", "neutral"

# 顺序敏感：先命中者胜（"打包提议" 必须先撞 "打包"，别被 "提议" 抢走无所谓，同区）
ZONE_RULES = (
    ("对账", ZONE_DATA), ("清欠", ZONE_DATA), ("台账", ZONE_DATA),
    ("核对", ZONE_DATA), ("状态", ZONE_DATA), ("统计", ZONE_DATA), ("账", ZONE_DATA),
    ("回溯碰撞", ZONE_PROP), ("打包", ZONE_PROP), ("簇", ZONE_PROP),
    ("提议", ZONE_PROP), ("提案", ZONE_PROP), ("碰撞", ZONE_PROP),
    ("建议", ZONE_PROP), ("合成", ZONE_PROP),
)

ZONE_HEAD = {
    ZONE_DATA: ("ripple", "数据区 · 台账事实", "可从台账与文件系统直接核对的账目与事实"),
    ZONE_PROP: ("bolt", "提议区 · AI 预填，裁定在用户", "以下为潮汐的判断与预填提案，不是既成事实"),
}

# ============================== 小灰字口径注 ==============================
FN_DATA = "数据区＝可从台账与文件系统直接核对的事实；口径见 soup-memory skill。"
FN_M4 = "M4 簇判定与合成草案皆为潮汐预填提案，裁定与实施在用户。"
FN_REPLAY = ("回溯碰撞＝潮汐定向重放（新卡碰旧题），闸门标准同会话闪电、宁缺毋滥；"
             "每条 Next step 皆待裁定。")
FN_PACK = "打包提议＝本期需要用户拍板事项的汇总清单。"

FOOT_EXACT = {
    "对账": FN_DATA, "清欠": FN_DATA,
    "簇检测": FN_M4, "提议": FN_M4,
    "回溯碰撞提案": FN_REPLAY, "打包提议": FN_PACK,
}
FOOT_FUZZY = (
    ("回溯碰撞", FN_REPLAY), ("打包", FN_PACK),
    ("对账", FN_DATA), ("清欠", FN_DATA),
    ("簇", FN_M4), ("提议", FN_M4),
)

ICON_RULES = (
    ("回溯碰撞", "bolt"), ("打包", "bundle"), ("簇", "mol"),
    ("提议", "mol"), ("提案", "bolt"), ("碰撞", "bolt"),
    ("对账", "ripple"), ("清欠", "ripple"), ("台账", "ripple"),
    ("状态", "ripple"), ("账", "ripple"),
)

FIELD_CLS = {
    "碰撞": "f-hit", "原文": "f-src", "推理": "f-why",
    "增量": "f-add", "Next step": "f-next",
}


def zone_for(name):
    for key, zone in ZONE_RULES:
        if key in name:
            return zone
    return ZONE_NEUTRAL


def footnote_for(name):
    if name in FOOT_EXACT:
        return FOOT_EXACT[name]
    for key, note in FOOT_FUZZY:
        if key in name:
            return note
    return ""


def icon_for(name):
    for key, ic in ICON_RULES:
        if key in name:
            return ic
    return "dot"


def field_cls(label):
    key = label.strip()
    if key in FIELD_CLS:
        return FIELD_CLS[key]
    if key.lower().startswith("next"):
        return "f-next"
    return "f-other"


# ============================== 内联 SVG ==============================
def _svg(inner, size=16, box=16, cls="ic"):
    return ('<svg class="%s" width="%d" height="%d" viewBox="0 0 %d %d" '
            'aria-hidden="true" focusable="false">%s</svg>') % (cls, size, size, box, box, inner)


ICONS = {
    # 潮汐池：一滴落水 + 两圈涟漪
    "ripple": _svg(
        '<circle cx="8" cy="2.4" r="1.15" fill="currentColor"/>'
        '<path d="M8 4.1v2.6" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" opacity=".7"/>'
        '<ellipse cx="8" cy="9.6" rx="3.1" ry="1.25" fill="none" stroke="currentColor" stroke-width="1.15"/>'
        '<ellipse cx="8" cy="9.9" rx="6.3" ry="2.7" fill="none" stroke="currentColor" stroke-width="1.05" opacity=".5"/>'),
    # 氨基酸分子簇：三球 + 键线
    "mol": _svg(
        '<path d="M4.3 5.2L11.6 4.2M4.3 5.2L8.7 11.4M11.6 4.2L8.7 11.4" '
        'stroke="currentColor" stroke-width="1.05" opacity=".65"/>'
        '<circle cx="4.3" cy="5.2" r="2.2" fill="currentColor" opacity=".9"/>'
        '<circle cx="11.6" cy="4.2" r="1.6" fill="none" stroke="currentColor" stroke-width="1.15"/>'
        '<circle cx="8.7" cy="11.4" r="2" fill="none" stroke="currentColor" stroke-width="1.15"/>'),
    # 闪电
    "bolt": _svg(
        '<path d="M9.6 1.4L3.9 8.6h3.3l-1 6L12.4 7H8.9z" fill="currentColor"/>'),
    # 打包清单
    "bundle": _svg(
        '<path d="M5.4 4.2h8M5.4 8h8M5.4 11.8h8" stroke="currentColor" '
        'stroke-width="1.2" stroke-linecap="round"/>'
        '<circle cx="2.5" cy="4.2" r="1.15" fill="currentColor"/>'
        '<circle cx="2.5" cy="8" r="1.15" fill="currentColor" opacity=".6"/>'
        '<circle cx="2.5" cy="11.8" r="1.15" fill="currentColor" opacity=".35"/>'),
    # 中性
    "dot": _svg(
        '<circle cx="8" cy="8" r="4.6" fill="none" stroke="currentColor" stroke-width="1.2"/>'
        '<circle cx="8" cy="8" r="1.3" fill="currentColor" opacity=".7"/>'),
}


def _wave_path(y0, amp, period, phase, w, h):
    """二次贝塞尔连缀出的平滑浪线，向下闭合成色块。"""
    x = -float(phase)
    parts = ["M%.1f %.1f" % (x, y0)]
    up = True
    while x < w:
        cx = x + period / 2.0
        nx = x + period
        cy = y0 - 2.0 * amp if up else y0 + 2.0 * amp
        parts.append("Q%.1f %.1f %.1f %.1f" % (cx, cy, nx, y0))
        x = nx
        up = not up
    parts.append("L%.1f %.1f L%.1f %.1f Z" % (w, h, -float(phase), h))
    return " ".join(parts)


def tide_band():
    """页头潮汐带：三层叠浪 + 上浮气泡 + 半沉的氨基酸分子 + 一道落海闪电（米勒实验）。"""
    w, h = 880.0, 92.0
    back = _wave_path(56, 5, 260, 40, w, h)
    mid = _wave_path(65, 6, 208, 150, w, h)
    front = _wave_path(74, 5, 322, 60, w, h)

    s = ['<svg class="band" viewBox="0 0 880 92" width="880" height="92" '
         'preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">']
    # 闪电落海（空中，最先画底光）
    s.append('<circle cx="196" cy="49" r="13" fill="#c25e3a" opacity=".10"/>')
    s.append('<circle cx="196" cy="49" r="5.5" fill="#c25e3a" opacity=".16"/>')
    s.append('<path d="M212 5L197 27h7.6l-11 22" fill="none" stroke="#c25e3a" '
             'stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round" opacity=".85"/>')
    # 空中的两颗气泡
    s.append('<circle cx="300" cy="40" r="1.6" fill="none" stroke="#4b8f83" stroke-width="1" opacity=".45"/>')
    s.append('<circle cx="629" cy="35" r="1.3" fill="none" stroke="#4b8f83" stroke-width="1" opacity=".38"/>')
    # 最后一层浪（远）
    s.append('<path d="%s" fill="#dbe9e4"/>' % back)
    # 水中气泡
    for cx, cy, r, op in ((296, 62, 2.6, .55), (309, 53, 1.8, .45), (287, 50, 1.3, .38),
                          (618, 60, 3.0, .5), (633, 49, 2.0, .42), (645, 42, 1.3, .35),
                          (430, 66, 2.2, .4), (441, 57, 1.4, .32)):
        s.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#2f6d63" '
                 'stroke-width="1" opacity="%s"/>' % (cx, cy, r, op))
    # 中层浪
    s.append('<path d="%s" fill="#a9c9c2" opacity=".8"/>' % mid)
    # 氨基酸分子簇（半沉在浪里）
    s.append('<g opacity=".92">'
             '<path d="M676 60L701 53M676 60L706 71M701 53L706 71M706 71L684 76" '
             'stroke="#b08b4f" stroke-width="1.2" opacity=".7"/>'
             '<circle cx="676" cy="60" r="4.4" fill="#b08b4f" opacity=".85"/>'
             '<circle cx="701" cy="53" r="3.1" fill="none" stroke="#b08b4f" stroke-width="1.3"/>'
             '<circle cx="706" cy="71" r="3.6" fill="#b08b4f" opacity=".5"/>'
             '<circle cx="684" cy="76" r="2.4" fill="none" stroke="#b08b4f" stroke-width="1.2"/>'
             '</g>')
    # 前层浪（近，深潮汐青）+ 浪脊高光
    s.append('<path d="%s" fill="#2f6d63" opacity=".92"/>' % front)
    s.append('<path d="%s" fill="none" stroke="#ffffff" stroke-width="1" opacity=".22"/>'
             % _wave_path(74, 5, 322, 60, w, h))
    s.append('</svg>')
    return "".join(s)


def foot_band():
    """页脚收尾细浪带。"""
    w, h = 880.0, 24.0
    a = _wave_path(11, 3.2, 240, 20, w, h)
    b = _wave_path(16, 4.0, 300, 130, w, h)
    return ('<svg class="band band-foot" viewBox="0 0 880 24" width="880" height="24" '
            'preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">'
            '<path d="%s" fill="#dbe9e4"/>'
            '<path d="%s" fill="#a9c9c2" opacity=".65"/>'
            '</svg>') % (a, b)


# ============================== 解析 ==============================
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
SEC_RE = re.compile(r"^\*\*(.+?)\*\*(.*)$")
LI_RE = re.compile(r"^[-*+]\s+(.*)$")
FIELD_RE = re.compile(r"^【([^】]*)】(.*)$")
RULE_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def parse(md):
    """宽容解析：已知结构建块，未知结构一律落成段落，绝不丢行。"""
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    title = None
    blocks = []
    sec = None
    card = None
    blank = True

    def container():
        if card is not None:
            return card["body"]
        if sec is not None:
            return sec["body"]
        return blocks

    for raw in lines:
        s = raw.strip()
        if not s:
            blank = True
            continue

        m = HEAD_RE.match(s)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1 and title is None:
                title = text
                card = None
                blank = False
                continue
            if level >= 3:
                # 提案卡：`### 提案N · 标题`，"·" 前的短前缀作编号徽章
                num, sep, rest = "", "", text
                if " · " in text:
                    head, tail = text.split(" · ", 1)
                    if len(head) <= 10:
                        num, sep, rest = head, " · ", tail
                c = {"t": "card", "num": num, "sep": sep, "title": rest,
                     "body": [], "blank": blank}
                (sec["body"] if sec is not None else blocks).append(c)
                card = c
                blank = False
                continue
            # `##` 或重复的 `#` → 版块（无导语）
            card = None
            sec = {"t": "sec", "name": text, "sep": "", "zone": zone_for(text),
                   "body": [], "blank": blank}
            blocks.append(sec)
            blank = False
            continue

        if s.startswith("⚡"):
            card = None
            sec = None
            blocks.append({"t": "zap", "text": s, "blank": blank})
            blank = False
            continue

        m = SEC_RE.match(s)
        if m:
            name = m.group(1).strip()
            rest = m.group(2)
            sepc = ""
            if rest[:1] in ("：", ":"):
                sepc, rest = rest[:1], rest[1:]
            card = None
            sec = {"t": "sec", "name": name, "sep": sepc, "zone": zone_for(name),
                   "body": [], "blank": blank}
            if rest.strip():
                sec["body"].append({"t": "p", "text": rest, "lead": True, "blank": False})
            blocks.append(sec)
            blank = False
            continue

        m = LI_RE.match(s)
        if m:
            item = m.group(1)
            if card is not None:
                mf = FIELD_RE.match(item)
                if mf:
                    card["body"].append({"t": "field", "label": mf.group(1),
                                         "text": mf.group(2), "blank": blank})
                    blank = False
                    continue
            cont = container()
            if cont and cont[-1]["t"] == "ul":
                cont[-1]["items"].append(item)
            else:
                cont.append({"t": "ul", "items": [item], "blank": blank})
            blank = False
            continue

        if RULE_RE.match(s):
            container().append({"t": "rule", "text": s, "blank": blank})
            blank = False
            continue

        container().append({"t": "p", "text": s, "blank": blank})
        blank = False

    return title, blocks


def extract_tail(blocks):
    """抽出结尾散段（如状态页备注）：末版块尾部、以空行起头、直到文末的纯段落。"""
    last = None
    for b in blocks:
        if b["t"] == "sec":
            last = b
    if last is None:
        return []
    body = last["body"]
    i = len(body)
    while i > 0 and body[i - 1]["t"] == "p" and not body[i - 1].get("lead"):
        i -= 1
    cut = None
    for j in range(i, len(body)):
        if body[j].get("blank"):
            cut = j
            break
    if cut is None:
        return []
    tail = body[cut:]
    del body[cut:]
    return tail


# ============================== 渲染 ==============================
def esc(s):
    return _html_escape(str(s), quote=False)


def inline(s):
    """行内 markdown：先 HTML 转义，再只处理 **粗体**，其余字符原样。"""
    out = esc(s)
    return BOLD_RE.sub(lambda m: "<strong>" + m.group(1) + "</strong>", out)


def render_p(item):
    cls = ' class="raw"' if item["text"].lstrip().startswith("|") else ""
    return "<p%s>%s</p>" % (cls, inline(item["text"]))


def render_item(item, out):
    t = item["t"]
    if t == "p":
        out.append(render_p(item))
    elif t == "ul":
        out.append('<ul class="bul">' +
                   "".join("<li>" + inline(x) + "</li>" for x in item["items"]) +
                   "</ul>")
    elif t == "rule":
        # 分隔线：图形化的同时把原字符留在 DOM 里，保证逐字可对账
        out.append('<hr class="mdrule"><span class="vh">' + esc(item["text"]) + "</span>")
    elif t == "field":
        render_field(item, out)
    elif t == "card":
        render_card(item, out)


def render_field(f, out):
    key = f["label"].strip()
    cls = field_cls(key)
    lab = ('<span class="fl"><span class="bk">【</span>' + esc(f["label"]) +
           '<span class="bk">】</span></span>')
    txt = '<span class="ft">' + inline(f["text"]) + "</span>"
    stamp = '<span class="stamp">待裁定</span>' if cls == "f-next" else ""
    # 注意：标签与正文必须无空白相连（同一 md 行不可被空白切断）；
    # 「待裁定」戳排在正文之后，靠 grid 定位回左栏第二行，不插进正文里。
    out.append('<div class="field ' + cls + '">' + lab + txt + stamp + "</div>")


def render_card(card, out):
    out.append('<article class="card">')
    head = '<div class="card-head">' + '<span class="card-ic">' + ICONS["bolt"] + "</span>"
    if card["num"]:
        head += ('<span class="pnum">' + esc(card["num"]) + "</span>" +
                 '<span class="pdot">' + esc(card["sep"]) + "</span>")
    head += '<span class="ptitle">' + inline(card["title"]) + "</span></div>"
    out.append(head)
    for it in card["body"]:
        render_item(it, out)
    out.append("</article>")


def render_section(sec, out):
    zone = sec["zone"]
    cls = {ZONE_DATA: "sec-data", ZONE_PROP: "sec-prop", ZONE_NEUTRAL: "sec-neutral"}[zone]
    badge = '<span class="badge b-prop">提案 · 待裁定</span>' if zone == ZONE_PROP else ""
    icon = '<span class="sec-ic">' + ICONS[icon_for(sec["name"])] + "</span>"
    sep = '<span class="vh">' + esc(sec["sep"]) + "</span>" if sec["sep"] else ""
    # 徽章排在 DOM 最前（靠 flex order 视觉右对齐），这样版块名与导语在文本流里仍然相连
    head = ('<div class="sec-head">' + badge + icon +
            '<span class="sec-name">' + esc(sec["name"]) + "</span>" + sep + "</div>")

    body = sec["body"]
    lead_html = ""
    rest = body
    if body and body[0]["t"] == "p" and body[0].get("lead"):
        lead_html = render_p(body[0])
        rest = body[1:]

    out.append('<section class="sec ' + cls + '">')
    out.append(head + '<div class="sec-body">' + lead_html)  # 同一行输出：不引入空白
    for it in rest:
        render_item(it, out)
    out.append("</div>")
    note = footnote_for(sec["name"])
    if note:
        out.append('<div class="section-foot">' + esc(note) + "</div>")
    out.append("</section>")


def zone_open(zone, out, suffix=""):
    icon, tag, hint = ZONE_HEAD[zone]
    out.append('<div class="zone zone-' + zone + '">')
    out.append('<div class="zone-head"><span class="zone-ic">' + ICONS[icon] + "</span>"
               '<span class="zone-tag">' + esc(tag + suffix) + "</span>"
               '<span class="zone-hint">' + esc(hint) + "</span></div>")


def render_body(blocks, tail):
    out = []
    cur = None  # 当前打开的分区
    for b in blocks:
        t = b["t"]
        if t == "sec":
            z = b["zone"]
            if z in ZONE_HEAD:
                if cur != z:
                    if cur:
                        out.append("</div>")
                    zone_open(z, out)
                    cur = z
            else:
                if cur:
                    out.append("</div>")
                    cur = None
            render_section(b, out)
            continue
        # 非版块的顶层块：先合上分区
        if cur:
            out.append("</div>")
            cur = None
        if t == "zap":
            body = inline(b["text"][1:])
            out.append('<div class="zap-banner"><span class="zap">' +
                       esc(b["text"][:1]) + "</span>" + body + "</div>")
        else:
            out.append('<section class="sec sec-neutral sec-bare"><div class="sec-body">')
            render_item(b, out)
            out.append("</div></section>")
    if cur:
        out.append("</div>")

    if tail:
        zone_open(ZONE_DATA, out, " · 尾注")
        out.append('<section class="sec sec-data sec-bare"><div class="sec-body">')
        for it in tail:
            render_item(it, out)
        out.append("</div></section>")
        out.append("</div>")
    return out


# ============================== 内容对账 ==============================
class _TextGrab(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.buf = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def text(self):
        return "".join(self.buf)


def fold(s):
    return re.sub(r"\s+", " ", s).strip()


def html_text(doc):
    p = _TextGrab()
    p.feed(doc)
    p.close()
    return p.text()


def md_line_text(line):
    s = line.strip()
    s = re.sub(r"^#{1,6}\s+", "", s)
    s = re.sub(r"^[-*+]\s+", "", s)
    s = s.replace("**", "")
    return fold(s)


def reconcile(md, doc):
    """html 去标签文本（折叠空白）须包含 md 每一非空行文本（折叠空白）。"""
    hay = fold(html_text(doc))
    total = 0
    missing = []
    for n, line in enumerate(md.replace("\r\n", "\n").replace("\r", "\n").split("\n"), 1):
        s = md_line_text(line)
        if not s:
            continue
        total += 1
        if s not in hay:
            missing.append((n, s))
    return total, missing


# ============================== 页面 ==============================
CSS = """
:root{
  color-scheme: light;
  --paper:#faf8f4; --card:#ffffff; --ink:#2b2b2b; --ink-soft:#33302b;
  --muted:#8a8377; --faint:#a09a8e; --line:#e8e2d8; --line-soft:#f0ebe2;
  --gold:#b08b4f; --gold-deep:#7a5c2e; --gold-wash:#f8f2e6;
  --tide:#2f6d63; --tide-mid:#4b8f83; --tide-pale:#dbe9e4; --tide-wash:#eff5f3;
  --zap:#c25e3a; --zap-deep:#a1492a; --zap-wash:#fdf0ec; --zap-line:#eec7ba;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:"Segoe UI","Microsoft YaHei",system-ui,sans-serif;
  background:var(--paper);color:var(--ink);font-size:14px;line-height:1.78;}
.page{max-width:880px;margin:0 auto;padding:26px 20px 40px;}
.vh{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;
  clip:rect(0,0,0,0);clip-path:inset(50%);white-space:nowrap;border:0;}

/* ---- 页头 ---- */
.eyebrow{font-size:11.5px;letter-spacing:.34em;color:var(--gold-deep);margin-bottom:7px;}
h1{font-size:21px;line-height:1.5;font-weight:700;color:#26241f;}
.head-meta{font-size:11.5px;color:var(--faint);margin-top:7px;line-height:1.7;}
.band{display:block;width:100%;height:auto;margin:6px 0 2px;}
.band-foot{margin:26px 0 8px;}

/* ---- 闪电横幅 ---- */
.zap-banner{background:var(--zap-wash);border:1px solid var(--zap-line);
  border-left:3px solid var(--zap);border-radius:10px;padding:11px 15px;
  color:#8c3a1e;line-height:1.8;margin:14px 0 4px;}
.zap-banner .zap{font-size:15px;margin-right:2px;}
.zap-banner strong{color:#7d2f14;}

/* ---- 分区 ---- */
.zone{margin:24px 0 0;}
.zone-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;
  padding-bottom:6px;border-bottom:1px solid var(--line);margin-bottom:12px;}
.zone-ic{display:inline-flex;}
.zone-tag{font-size:12.5px;font-weight:700;letter-spacing:.03em;}
.zone-hint{font-size:11.5px;color:var(--faint);font-weight:400;}
.zone-data .zone-ic,.zone-data .zone-tag{color:var(--tide);}
.zone-prop .zone-ic,.zone-prop .zone-tag{color:var(--zap);}

/* ---- 版块 ---- */
.sec{background:var(--card);border:1px solid var(--line);border-left-width:3px;
  border-radius:10px;padding:12px 16px 13px;margin-bottom:11px;}
.sec-data{border-left-color:var(--tide);}
.sec-prop{border-left-color:var(--zap);}
.sec-neutral{border-left-color:#d9d3c6;}
.sec-bare{padding-top:11px;}
.sec-head{display:flex;align-items:center;gap:7px;margin-bottom:7px;position:relative;}
.sec-ic{display:inline-flex;}
.sec-data .sec-ic{color:var(--tide);}
.sec-prop .sec-ic{color:var(--zap);}
.sec-neutral .sec-ic{color:#b3ab9c;}
.sec-name{font-size:14.5px;font-weight:700;color:#3a372f;letter-spacing:.02em;}
.badge{order:9;margin-left:auto;font-size:11px;line-height:1.7;padding:1px 9px;
  border-radius:999px;border:1px solid;white-space:nowrap;font-weight:600;}
.b-prop{color:var(--zap-deep);background:#fbeee8;border-color:var(--zap-line);}
.sec-body p{margin:7px 0;line-height:1.82;color:var(--ink-soft);}
.sec-body p:first-child{margin-top:0;}
.sec-body p.raw{font-family:Consolas,"Courier New",monospace;font-size:12.5px;
  white-space:pre-wrap;color:#4a453d;}
.sec-body strong{color:var(--gold-deep);font-weight:700;}
.sec-prop .sec-body strong{color:#8c4a24;}
ul.bul{margin:7px 0 7px 20px;}
ul.bul li{margin:4px 0;line-height:1.8;color:var(--ink-soft);}
ul.bul li::marker{color:var(--gold);}
hr.mdrule{border:0;border-top:1px solid var(--line-soft);margin:12px 0;}
.section-foot{margin-top:10px;font-size:11.5px;color:var(--faint);line-height:1.65;}

/* ---- 提案卡 ---- */
.card{background:#fffcf7;border:1px solid #ece2cf;border-radius:9px;
  padding:11px 14px 12px;margin:11px 0;}
.card-head{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap;
  padding-bottom:8px;margin-bottom:4px;border-bottom:1px dashed #e8dfcd;}
.card-ic{color:var(--zap);align-self:center;display:inline-flex;}
.pnum{font-size:13px;font-weight:700;color:var(--gold-deep);letter-spacing:.03em;
  white-space:nowrap;}
.pdot{color:#c9c0ae;}
.ptitle{font-size:14px;font-weight:600;color:#332f28;line-height:1.65;}
.field{display:grid;grid-template-columns:94px 1fr;gap:2px 10px;
  padding:6px 0;border-top:1px solid #f2ece0;}
.card-head + .field{border-top:0;}
.fl{font-size:12.5px;font-weight:600;line-height:1.85;white-space:nowrap;}
.bk{opacity:.4;font-weight:400;}
.ft{font-size:13.5px;line-height:1.85;color:var(--ink-soft);}
.f-hit .fl{color:var(--zap);}
.f-src .fl{color:var(--muted);}
.f-src .ft{color:#5a5348;}
.f-why .fl{color:var(--tide);}
.f-add .fl{color:var(--gold-deep);}
.f-other .fl{color:#6b6357;}
/* Next step 单独提亮；「待裁定」戳在 DOM 里排在正文之后（不切断 md 原句），
   靠 grid 定位回左栏第二行，贴着标签下方 */
.f-next{background:var(--gold-wash);border:1px solid #ecdfc4;border-radius:8px;
  padding:8px 11px;margin-top:7px;grid-template-rows:auto 1fr;}
.f-next .fl{grid-column:1;grid-row:1;color:var(--gold-deep);font-weight:700;}
.f-next .ft{grid-column:2;grid-row:1 / span 2;color:#3b352a;}
.f-next .stamp{grid-column:1;grid-row:2;justify-self:start;align-self:start;
  margin-top:3px;font-size:10.5px;line-height:1.7;padding:0 7px;border-radius:999px;
  color:var(--zap-deep);background:#fbeee8;border:1px solid var(--zap-line);
  white-space:nowrap;}

/* ---- 页脚 ---- */
.foot{font-size:11.5px;color:var(--faint);line-height:1.8;}
.foot-sep{color:#cfc8ba;}

@media (max-width:640px){
  .page{padding:18px 14px 32px;}
  .field{grid-template-columns:1fr;}
  .f-next{grid-template-rows:auto;}
  .f-next .fl,.f-next .ft,.f-next .stamp{grid-column:1;grid-row:auto;}
  .fl{white-space:normal;}
}
@media print{
  body{background:#fff;}
  .page{padding:0;}
  .sec,.card,.zap-banner{break-inside:avoid;page-break-inside:avoid;}
  .zone{break-before:auto;}
}
"""

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>__CSS__</style>
</head>
<body>
<div class="page">
<header class="tide-head">
<div class="eyebrow">原始汤</div>
<h1>__H1__</h1>
<div class="head-meta">数据源 __SRC__ · 全静态页面（无脚本），内容与 md 逐段一致</div>
</header>
__BAND__
__BODY__
__FOOTBAND__
<div class="foot">
<span id="gen-stamp">生成时间 __STAMP__</span><span class="foot-sep"> · </span>生成器 __GEN__<span class="foot-sep"> · </span>数据源 __SRC__
</div>
<div class="foot">本页由 md 直出：__CHECK__。要改内容请改 md 后重跑生成器，勿直接编辑 html。</div>
</div>
</body>
</html>
"""


def build(md, src_label, stamp):
    title, blocks = parse(md)
    tail = extract_tail(blocks)
    body = "\n".join(render_body(blocks, tail))
    h1 = title if title else "潮汐周报"
    doc = (PAGE
           .replace("__CSS__", CSS)
           .replace("__TITLE__", esc(h1))
           .replace("__H1__", inline(h1))
           .replace("__BAND__", tide_band())
           .replace("__FOOTBAND__", foot_band())
           .replace("__BODY__", body)
           .replace("__STAMP__", esc(stamp))
           .replace("__GEN__", esc(GEN_PATH_LABEL))
           .replace("__SRC__", esc(src_label)))
    total, missing = reconcile(md, doc)
    if missing:
        check = "内容对账 %d/%d 段落文本已落页，%d 段缺失（见生成日志）" % (
            total - len(missing), total, len(missing))
    else:
        check = "内容对账 %d/%d 段落文本已落页" % (total, total)
    return doc.replace("__CHECK__", esc(check)), total, missing


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("用法：py 潮汐周报生成器.py <周报md路径> [输出html路径]\n")
        return 2
    src = argv[1]
    if not os.path.isfile(src):
        sys.stderr.write("找不到周报文件：%s\n" % src)
        return 1
    out_path = argv[2] if len(argv) > 2 else os.path.splitext(src)[0] + ".html"

    with open(src, encoding="utf-8-sig") as f:
        md = f.read()

    parent = os.path.basename(os.path.dirname(os.path.abspath(src)))
    src_label = (parent + "/" if parent else "") + os.path.basename(src)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    doc, total, missing = build(md, src_label, stamp)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)

    print("written: %s" % out_path)
    if missing:
        print("内容对账：%d/%d —— 以下 md 行未在 html 文本中找到：" % (total - len(missing), total))
        for n, s in missing:
            print("  第 %d 行：%s" % (n, s[:120]))
        return 3
    print("内容对账：%d/%d 全部落页" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
