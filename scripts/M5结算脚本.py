# -*- coding: utf-8 -*-
"""M5 有效性结算脚本 · 2026-08-12
确定性算分，模型只解读。
复用闪电抽样器的台账解析（子进程调用，取【逐行解析审计】段），
不重写解析逻辑——效能量化卡"结算与消融共用台账解析代码"的落实。

指标口径（机制清单 M5 + 2026-08-10 结算口径修订）：
  指标1 北极星：未解问题关闭数 = 各卡「未解问题」栏内含「→ 已由」标注的条目数
  指标2：碰撞改变结论数 = 台账行级裁定「强认可」计数（2026-08-10 起以强认可为准）
  监测线：静默率（卡×会话对级）；强认可占呈现行比（>60% 判判据漂移）
  静默审计：从静默对中定抽样本（seed=20260812），另加台账预标注的假阴性候补
# ── 通用改造版── 默认行为与原版同语义；仅改解释器选择与报错：
#    R5 解释器：子进程以 sys.executable（当前解释器）优先，兜底按 py→python→python3 探测（shutil.which）；
#       spawn 失败（FileNotFoundError/OSError）/ returncode==9009 / stdout 空 → 明确报错
#       （含实际 returncode 与提示「请确认 Python 解释器可用；或用 --sampler 显式指定抽样器路径」）；
#       新增 --sampler 路径 参数（默认 <root>/_氨基酸库/闪电抽样器.py）。
#    R6 编码：stdout/stderr 均 reconfigure(encoding="utf-8")。
#    发现21 口径分叉：报告末尾追加卡级/行级口径标注（不改统计行为）。
"""
import re, sys, subprocess, random, shutil, argparse
from pathlib import Path

# ---------- R6：stdout/stderr 均按 UTF-8 输出（Windows 重定向/管道下避免本地编码乱码） ----------
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


def pick_interpreter():
    """R5：优先复用当前解释器（sys.executable）；兜底 py→python→python3 探测。
    python3 在 Windows 上最易命中 WindowsApps 存根（returncode 9009），故排最后。"""
    if sys.executable:
        return sys.executable
    for name in ("py", "python", "python3"):
        found = shutil.which(name)
        if found:
            return found
    return None


def parse_args():
    ap = argparse.ArgumentParser(
        description="M5 有效性结算脚本（DSH 移植版）：确定性算分，复用抽样器台账解析。")
    ap.add_argument("root", help="原始汤根目录（夹具或真库均可）")
    ap.add_argument("--sampler", default=None,
                    help="抽样器脚本路径；默认 <root>/_氨基酸库/闪电抽样器.py")
    return ap.parse_args()


args = parse_args()
ROOT = Path(args.root)
SEED_AUDIT = 20260812

# ---------- 1. 调抽样器取解析审计（R5：解释器探测 + 明确报错） ----------
interp = pick_interpreter()
if interp is None:
    sys.exit("错误：未找到可用的 Python 解释器（sys.executable 为空，且 py/python/python3 均不可探测）。\n"
             "请确认 Python 解释器可用；或用 --sampler 显式指定抽样器路径")
sampler = Path(args.sampler) if args.sampler else ROOT / "_氨基酸库" / "闪电抽样器.py"
if not sampler.exists():
    sys.exit(f"错误：抽样器脚本不存在：{sampler}\n"
             "请确认 Python 解释器可用；或用 --sampler 显式指定抽样器路径")
cmd = [interp, str(sampler), str(ROOT), "--seed", "1"]
try:
    proc = subprocess.run(cmd, capture_output=True, text=True)
except (FileNotFoundError, OSError) as e:
    sys.exit(f"错误：无法启动抽样器子进程（命令：{' '.join(cmd)}）：{e}\n"
             "请确认 Python 解释器可用；或用 --sampler 显式指定抽样器路径")
if proc.returncode == 9009 or proc.returncode != 0 or not proc.stdout.strip():
    detail = (f"（stderr：{proc.stderr.strip()[:200]}）" if proc.stderr.strip() else "")
    sys.exit(f"错误：抽样器子进程未成功产出解析审计（returncode={proc.returncode}，"
             f"stdout {len(proc.stdout)} 字符{detail}）。\n"
             "请确认 Python 解释器可用；或用 --sampler 显式指定抽样器路径")
out = proc.stdout
try:
    audit = out.split("【逐行解析审计】")[1].split("【告警区】")[0]
    warns = out.split("【告警区】")[1].split("【权重表】")[0]
except IndexError:
    sys.exit("错误：抽样器输出结构异常，无法解析（子进程已正常退出、stdout 非空，但缺少"
             "【逐行解析审计】/【告警区】/【权重表】段落标记）。\n"
             "请确认 --sampler 指定的确为闪电抽样器脚本，或检查其输出格式")

rows = []  # dict: n, date, session, drawn[], shown[], silent[], verdict
cur = None
for line in audit.splitlines():
    m = re.match(r"\s*第\s*(\d+)\s*行\s+(\S+)\s*│\s*(.+)$", line)
    if m:
        cur = {"n": int(m.group(1)), "date": m.group(2), "session": m.group(3).strip(),
               "drawn": [], "shown": [], "silent": [], "verdict": None, "nonsample": False}
        rows.append(cur); continue
    if cur is None: continue
    s = line.strip()
    if "非抽样行" in s: cur["nonsample"] = True
    for key, tag in (("drawn", "抽中："), ("shown", "呈现："), ("silent", "静默：")):
        if s.startswith(tag):
            body = s[len(tag):].strip()
            cur[key] = [] if body in ("（无）", "") else [c.strip() for c in body.split("｜") if c.strip()]
    if s.startswith("裁定："):
        cur["verdict"] = s[len("裁定："):].strip()

sample_rows = [r for r in rows if not r["nonsample"]]

# ---------- 2. 台账指标 ----------
drawn_pairs  = sum(len(r["drawn"])  for r in sample_rows)
shown_pairs  = sum(len(r["shown"])  for r in sample_rows)
silent_pairs = sum(len(r["silent"]) for r in sample_rows)
shown_rows   = [r for r in sample_rows if r["shown"]]
all_silent_rows = [r for r in sample_rows if r["drawn"] and not r["shown"]]
verdicts = {}
for r in shown_rows:
    verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
strong = verdicts.get("强认可", 0)
approve = verdicts.get("认可", 0)
pending_rows = [r["session"] for r in shown_rows if r["verdict"] == "待补"]

# ---------- 3. M2 关闭回写扫描 ----------
closed, opened, revised = [], 0, []
for card in sorted(ROOT.glob("*/_氨基酸.md")):
    text = card.read_text(encoding="utf-8")
    mm = re.search(r"##\s*未解问题\s*\n(.*?)(?=\n##|\Z)", text, re.S)
    if mm:
        for ln in mm.group(1).splitlines():
            if re.match(r"\s*[-*]\s+\S", ln):
                if "→ 已由" in ln:
                    closed.append((card.parent.name, ln.strip()[:120]))
                else:
                    opened += 1
    for ln in text.splitlines():
        if "→ 已被" in ln and "修正" in ln:
            revised.append((card.parent.name, ln.strip()[:120]))

# ---------- 4. 静默审计抽样 ----------
preflagged = [(r["session"], c) for r in rows for c in r["silent"]
              if "Opus5" in r["session"] and "FDE" in c]
pool = [(r["session"], c) for r in sample_rows for c in r["silent"]
        if (r["session"], c) not in preflagged]
rng = random.Random(SEED_AUDIT)
audit_sample = rng.sample(pool, min(3, len(pool)))

# ---------- 5. 输出 ----------
W = lambda *a: print(*a)
W("=" * 72)
W("M5 有效性结算 · 确定性指标报告（seed_audit=%d）" % SEED_AUDIT)
W("=" * 72)
W(f"台账解析：数据行 {len(rows)}（抽样行 {len(sample_rows)}，非抽样行 {len(rows)-len(sample_rows)}）")
W(f"卡池：{len(list(ROOT.glob('*/_氨基酸.md')))} 颗氨基酸落盘")
W()
W("【指标1 · 北极星：未解问题关闭数】")
W(f"  关闭 {len(closed)} 条 ｜ 仍开放 {opened} 条 ｜ 另有核心结论修正回写 {len(revised)} 条")
for f, ln in closed: W(f"    · {f} ｜ {ln}")
if revised:
    W("  修正回写（不计入指标1，附列）：")
    for f, ln in revised: W(f"    · {f} ｜ {ln}")
W()
W("【指标2 · 碰撞改变结论数（行级强认可）】")
W(f"  强认可 {strong} 行")
W(f"  裁定分布（呈现行 {len(shown_rows)}）：" + "、".join(f"{k}={v}" for k, v in sorted(verdicts.items())))
W()
W("【监测线】")
W(f"  卡×会话对：抽中 {drawn_pairs} ｜ 呈现 {shown_pairs} ｜ 静默 {silent_pairs}")
W(f"  静默率（对级）= {silent_pairs}/{drawn_pairs} = {silent_pairs/drawn_pairs:.1%}"
  "（预注册：语料多样化后应升至40-60%；50卡时仍≤20%判闸门过松）")
W(f"  行级呈现率 = {len(shown_rows)}/{len(sample_rows)} = {len(shown_rows)/len(sample_rows):.1%}")
W(f"  强认可占呈现行比 = {strong}/{len(shown_rows)} = {strong/len(shown_rows):.1%}（>60% 判判据向体感漂移）")
W(f"  端到端产率（行级，强认可+认可 ÷ 抽样行）= {(strong+approve)}/{len(sample_rows)} = {(strong+approve)/len(sample_rows):.1%}")
W(f"  待补裁定行 {len(pending_rows)}：" + "；".join(pending_rows) if pending_rows else "  待补裁定行 0")
W()
W("【静默审计样本】")
W("  预标注假阴性候补（台账 2026-08-12 归档补记）：")
for s, c in preflagged: W(f"    ◆ {s} × {c}")
W(f"  定抽样本（seed={SEED_AUDIT}，从其余 {len(pool)} 个静默对中抽 {len(audit_sample)}）：")
for s, c in audit_sample: W(f"    ○ {s} × {c}")
W()
W("【抽样器告警区转录】")
for ln in warns.strip().splitlines(): W("  " + ln.strip())
W()
# 发现21：口径分叉提示（不改统计行为，仅标注）
W("注：卡级裁定句式〔卡级裁定：…〕行的强认可不计入本指标2（行级口径），与抽样器赫布（卡级口径）可能不一致。")
