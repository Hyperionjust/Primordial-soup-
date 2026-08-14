#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 闪电抽样器（M3）：读各对话文件夹的 _氨基酸.md 与 _氨基酸库/闪电台账.md，
# 按「赫布上调 / 蔡格尼克保温 / 遗忘衰减」算权重，抽 1 颗野卡（均匀，保底意外性）
# + n-1 颗加权卡（无放回）。台账数据行 <10 时退化为全池均匀抽样。
# M4 修订（2026-08-10）：_氨基酸库/蛋白质：*.md 以升级权重入池（基线=成员最大值，叠乘自身因子），
# 成员不退池；同族去重＝蛋白质与其任一成员不同出（后到让位），成员相互之间不受限。
# M5 结算修订（2026-08-12，用户拍板）：备注含〔卡级裁定：卡全名=档；…〕句式的行按卡取裁定，
# 仅档位=强认可的卡获赫布 ×2；无该句式的行按行级裁定回退——修复「行级赫布无法按卡排除」口径误差。
# 用法：python3 闪电抽样器.py <原始汤根目录> [--exclude 文件夹名]... [--seed 整数] [--n 抽取数]
# 纯只读：除 stdout 外零副作用。规格见 机制：闪电的进化与有效性判据/机制清单.md。
# ── 通用改造版── 默认行为与原版逐字节同语义；新增：
#    R1 范围守卫（root/台账存在性预检，友好报错替代 FileNotFoundError traceback）+ --strict（INDEX 行数与磁盘卡文件夹数一致性校验）；
#    R2 权重参数 CLI 化（--hebb/--zeig-closed/--decay/--floor/--min-rows，默认=原常量，已接入权重/退化判定计算）；
#    R6 编码口径（stdout/stderr reconfigure utf-8；读文件 utf-8-sig）。详见仓库 README。
import sys, os, re, glob, random, argparse, unicodedata

HEBB = 2.0         # 强认可且实际呈现过 → ×2（状态制，只乘一次，禁止按次复利；2026-08-10 起改挂强认可，普通认可不加权）
ZEIG_CLOSED = 0.5  # 未解问题有条目且全部关闭 → ×0.5
DECAY = 0.7        # 末尾连续「抽中未呈现」每满 3 次 → ×0.7
FLOOR = 0.1        # 最终权重下限
MIN_ROWS = 10      # 台账数据行 <10 → 退化模式

SILENCE = ("无有效碰撞（静默）", "无碰撞（静默）", "未重复呈现")
CARDV = re.compile(r"卡级裁定：([^〔〕]+)〕")  # 2026-08-12 M5结算：拆分裁定规范句式
VERDICT_LEVELS = ("强认可", "认可", "无感", "反对")
NAME_HEAD = re.compile(r"\s*(.*?)[两三四五六七八九十]?卡")  # 「dbskill/graph两卡…」→ dbskill/graph
SEG = re.compile(r"[；。\n]")
SEP = re.compile(r"[、/，,]")
ONLY = re.compile(r"仅([^）)]+)")


def read(p):
    with open(p, encoding="utf-8-sig") as f:
        return f.read()


def core(name):
    """去掉「类型：」前缀。文件夹曾改前缀（台账写机制：X，磁盘为产品：X），故须前缀无关比较。"""
    i = name.find("：")
    return name[i + 1:] if i >= 0 else name


def dw(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, n):
    return s + " " * max(0, n - dw(s))


def parse_table(md):
    """取 Markdown 表体行（去表头与分隔行），每行返回单元格列表。"""
    rows = []
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")[1:-1]]
        if not cells or re.fullmatch(r"[-:\s]*", "".join(cells)):
            continue
        rows.append(cells)
    return rows[1:]


class Resolver:
    """卡名三级匹配：① 精确 ② 前缀无关 ③ 子串唯一。任一级须唯一命中。"""

    def __init__(self, folders):
        self.folders = folders

    def resolve(self, token):
        t = (token or "").strip()
        if not t:
            return None, "空名"
        if t in self.folders:
            return t, None
        k = core(t)
        hit = [f for f in self.folders if core(f) == k]
        if len(hit) == 1:
            return hit[0], None
        if len(hit) > 1:
            return None, "前缀无关匹配歧义（%s）" % "、".join(hit)
        hit = [f for f in self.folders if k in f]
        if len(hit) == 1:
            return hit[0], None
        if len(hit) > 1:
            return None, "子串匹配歧义（%s）" % "、".join(hit)
        return None, "未命中磁盘上任何卡"


def silence_tokens(note):
    """从备注抽出被静默限定的卡名 token。返回 (tokens, 解析失败的段落)。"""
    out, bad = [], []
    for seg in SEG.split(note):
        if not any(m in seg for m in SILENCE):
            continue
        m = NAME_HEAD.match(seg)
        toks = [t.strip() for t in SEP.split(m.group(1))] if m else []
        toks = [t for t in toks if t]
        if toks:
            out.extend(toks)
        else:
            bad.append(seg.strip())
    return out, bad


def weighted_pop(items, weights, rng):
    """按权重无放回取一个，返回索引。"""
    x = rng.random() * sum(weights)
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        if x < acc:
            return i
    return len(items) - 1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):  # R6：stderr 一并 UTF-8（原版仅 reconfigure stdout）
        sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="原始汤闪电 M3 加权抽样器（只读）")
    ap.add_argument("root", help="原始汤根目录")
    ap.add_argument("--exclude", action="append", default=[], metavar="文件夹名", help="抽样前从池中移除（可多次）")
    ap.add_argument("--seed", type=int, default=None, help="随机种子；不给则取系统熵（仍会打印）")
    ap.add_argument("--n", type=int, default=3, help="抽取数，默认 3")
    # R2：权重参数 CLI 化（默认=原模块常量，缺省时输出与原版逐字节一致）
    ap.add_argument("--hebb", type=float, default=HEBB,
                    help="强认可且实际呈现过 → 权重 ×此值（状态制，只乘一次，禁止按次复利；默认 %.1f）" % HEBB)
    ap.add_argument("--zeig-closed", type=float, default=ZEIG_CLOSED,
                    help="未解问题有条目且全部关闭 → ×此值（蔡格尼克保温；默认 %.1f）" % ZEIG_CLOSED)
    ap.add_argument("--decay", type=float, default=DECAY,
                    help="末尾连续「抽中未呈现」每满 3 次 → ×此值（遗忘衰减底数；默认 %.1f）" % DECAY)
    ap.add_argument("--floor", type=float, default=FLOOR,
                    help="最终权重下限（默认 %.1f）" % FLOOR)
    ap.add_argument("--min-rows", type=int, default=MIN_ROWS,
                    help="台账数据行低于此值 → 退化模式全池均匀抽样（默认 %d）" % MIN_ROWS)
    ap.add_argument("--strict", action="store_true",
                    help="R1 扩展：校验 _氨基酸库\\INDEX.md 存在且 INDEX 数据行数与磁盘卡文件夹数一致（默认不读 INDEX，保持原语义）")
    a = ap.parse_args()
    if a.n < 1:
        ap.error("--n 必须 ≥1")
    if a.hebb <= 0 or a.zeig_closed <= 0 or a.decay <= 0 or a.floor <= 0:
        ap.error("权重参数必须为正数")
    if a.min_rows < 1:
        ap.error("--min-rows 必须 ≥1")

    root = a.root
    # R1：范围守卫前置校验（替代原版的 FileNotFoundError traceback）
    if not os.path.isdir(root):
        sys.stderr.write("错误：未找到根目录（期望路径 %s）\n" % os.path.abspath(root))
        return 1
    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(2 ** 32)
    rng = random.Random(seed)

    notes = []  # (级别, 文本, 行号)
    warn = lambda m, r=None: notes.append(("告警", m, r))
    hint = lambda m, r=None: notes.append(("提示", m, r))

    # ── 全池发现 ────────────────────────────────────────────────
    cards = {}
    for p in sorted(glob.glob(os.path.join(root, "*", "_氨基酸.md"))):
        f = os.path.basename(os.path.dirname(p))
        if f == "_氨基酸库":
            continue
        cards[f] = os.path.abspath(p)
    folders = sorted(cards)
    if not folders:
        print("错误：在 %s 下未发现任何 <文件夹>/_氨基酸.md" % os.path.abspath(root))
        return 1

    # R1 台账存在性预检（放在卡发现之后：空目录报「未发现任何卡」保持与原版一致，
    # 有卡无台账才报台账缺失——fixture 冒烟 s2e 发现并修正的预检顺序）
    ledger_p = os.path.join(root, "_氨基酸库", "闪电台账.md")
    if not os.path.isfile(ledger_p):
        sys.stderr.write("错误：未找到 _氨基酸库\\闪电台账.md（期望路径 %s）\n" % os.path.abspath(ledger_p))
        return 1

    # R1 --strict：INDEX 存在 + 数据行数 == 磁盘卡文件夹数（蛋白质不进 INDEX，契约基线 16）
    if a.strict:
        index_p = os.path.join(root, "_氨基酸库", "INDEX.md")
        if not os.path.isfile(index_p):
            sys.stderr.write("错误：--strict 需要 _氨基酸库\\INDEX.md（期望路径 %s）\n" % os.path.abspath(index_p))
            return 1
        idx_rows = parse_table(read(index_p))
        if len(idx_rows) != len(folders):
            sys.stderr.write("错误：--strict INDEX 数据行数 %d 与磁盘卡文件夹数 %d 不一致（期望路径 %s）\n" % (
                len(idx_rows), len(folders), os.path.abspath(index_p)))
            return 1

    # ── 蛋白质发现（M4 修订 2026-08-10：成员不退池，蛋白质升权入池） ──
    proteins = {}  # 蛋白质名 → 成员文件夹名列表（按卡内「## 成员卡」节解析）
    amino_R = Resolver(folders)
    for p in sorted(glob.glob(os.path.join(root, "_氨基酸库", "蛋白质：*.md"))):
        name = os.path.splitext(os.path.basename(p))[0]
        cards[name] = os.path.abspath(p)
        members, inm = [], False
        for line in read(p).splitlines():
            if line.startswith("## 成员卡"):
                inm = True
                continue
            if line.startswith("## "):
                inm = False
            if inm and line.strip().startswith("- "):
                t = line.strip()[2:].split("（")[0].split("｜")[0].strip()
                f, why = amino_R.resolve(t)
                if f is None:
                    warn("蛋白质「%s」成员「%s」%s，不计入同族" % (name, t, why))
                elif f not in members:
                    members.append(f)
        if not members:
            warn("蛋白质「%s」未解析出任何成员卡，同族去重对其失效" % name)
        proteins[name] = members
    protein_names = sorted(proteins)
    all_names = folders + protein_names
    R = Resolver(all_names)

    # ── 蔡格尼克保温 ────────────────────────────────────────────
    zeig = {}
    for f in all_names:
        has, total, closed, inq = False, 0, 0, False
        for line in read(cards[f]).splitlines():
            if line.startswith("## 未解问题"):
                inq = has = True
                continue
            if line.startswith("## "):
                inq = False
            if inq and line.startswith("- "):
                total += 1
                if "已由" in line or "已被" in line:
                    closed += 1
        if not has:
            warn("卡「%s」缺少「## 未解问题」节（模板违规），蔡格尼克记 ×1.0" % f)
            zeig[f] = 1.0
        elif total == 0:
            hint("卡「%s」的「## 未解问题」节存在但零条目，蔡格尼克记 ×1.0" % f)
            zeig[f] = 1.0
        else:
            zeig[f] = a.zeig_closed if closed == total else 1.0

    # ── 台账解析 ────────────────────────────────────────────────
    rows = parse_table(read(os.path.join(root, "_氨基酸库", "闪电台账.md")))
    hebb, streak, audit = set(), {f: 0 for f in all_names}, []
    for i, r in enumerate(rows, 1):
        r = (r + [""] * 6)[:6]
        date, sess, drawn_cell, shown_cell, verdict, note = r

        if "未执行随机抽样" in drawn_cell:
            hint("第 %d 数据行「%s」标注未执行随机抽样，不参与权重统计" % (i, sess), i)
            audit.append((i, date, sess, None, None, verdict))
            continue

        drawn = []
        for t in drawn_cell.split("、"):
            if not t.strip():
                continue
            f, why = R.resolve(t)
            if f is None:
                warn("台账卡名「%s」%s，已跳过" % (t.strip(), why), i)
            elif f not in drawn:
                drawn.append(f)

        if not shown_cell.startswith("是"):
            if not shown_cell.startswith("否"):
                warn("「是否呈现」列取值「%s」无法识别，按「否」（全部静默）处理" % shown_cell, i)
            presented = []
        else:
            m = ONLY.search(shown_cell)
            if m:
                presented = []
                for t in SEP.split(m.group(1)):
                    f, why = R.resolve(t)
                    if f is None:
                        warn("「是（仅%s）」中的名「%s」%s，已忽略" % (m.group(1), t.strip(), why), i)
                    elif f not in drawn:
                        warn("「仅」限定的「%s」不在抽中列表，已忽略" % f, i)
                    else:
                        presented.append(f)
            else:
                presented = list(drawn)

        toks, bad = silence_tokens(note)
        for seg in bad:
            warn("备注含静默标记但未能解析出卡名：%s" % seg, i)
        for t in toks:
            f, why = R.resolve(t)
            if f is None:
                warn("备注静默限定名「%s」%s，静默未生效" % (t, why), i)
            elif f not in drawn:
                warn("备注静默限定名「%s」→「%s」不在抽中列表，已忽略" % (t, f), i)
            elif f in presented:
                presented.remove(f)

        cardv = {}
        for block in CARDV.findall(note):
            for seg in block.split("；"):
                seg = seg.strip()
                if not seg:
                    continue
                if "=" not in seg:
                    warn("卡级裁定段「%s」缺少=，已忽略" % seg, i)
                    continue
                t, v = seg.rsplit("=", 1)
                v = v.strip()
                if v not in VERDICT_LEVELS:
                    warn("卡级裁定「%s」档位「%s」不可识别，已忽略" % (t.strip(), v), i)
                    continue
                f, why = R.resolve(t)
                if f is None:
                    warn("卡级裁定名「%s」%s，已忽略" % (t.strip(), why), i)
                elif f not in drawn:
                    warn("卡级裁定名「%s」不在抽中列表，已忽略" % f, i)
                else:
                    cardv[f] = v
        if cardv:  # 2026-08-12 M5结算修订：有卡级句式的行按卡取裁定，仅强认可卡 ×2
            for f in presented:
                if cardv.get(f) == "强认可":
                    hebb.add(f)
                elif f not in cardv:
                    warn("呈现卡「%s」未见于本行卡级裁定句式，赫布按无强认可处理" % f, i)
        elif "强认可" in verdict:  # 行级回退：2026-08-10 起赫布只认强认可；子串包含判断天然区分「认可」
            hebb.update(presented)
        for f in drawn:
            streak[f] = 0 if f in presented else streak[f] + 1
        audit.append((i, date, sess, drawn, presented, verdict))

    # ── 权重 ────────────────────────────────────────────────────
    wt = {}
    for f in folders:
        h = a.hebb if f in hebb else 1.0
        d = a.decay ** (streak[f] // 3)
        wt[f] = (h, zeig[f], d, max(a.floor, 1.0 * h * zeig[f] * d))
    pbase = {}  # 蛋白质权重基线＝成员最终权重最大值（实时取值），其上叠乘自身因子
    for f in protein_names:
        mems = [m for m in proteins[f] if m in wt]
        base = max([wt[m][3] for m in mems], default=1.0)
        pbase[f] = base
        h = a.hebb if f in hebb else 1.0
        d = a.decay ** (streak[f] // 3)
        wt[f] = (h, zeig[f], d, max(a.floor, base * h * zeig[f] * d))

    # ── 排除 ────────────────────────────────────────────────────
    excluded = []
    for t in a.exclude:
        f, why = R.resolve(t)
        if f is None:
            warn("--exclude「%s」%s，未生效" % (t, why))
        else:
            excluded.append(f)
    pool = [f for f in all_names if f not in excluded]

    degenerate = len(rows) < a.min_rows
    n = a.n

    # ── 输出 ────────────────────────────────────────────────────
    print("═" * 76)
    print("闪电抽样器 · M3 加权随机 + 野卡槽")
    print("═" * 76)
    print("seed：%d%s" % (seed, "（本次指定）" if a.seed is not None else "（系统熵，复现请加 --seed %d）" % seed))
    print("根目录：%s" % os.path.abspath(root))
    print("模式：%s（台账数据行 %d %s %d）" % (
        "退化·全池均匀抽样" if degenerate else "加权抽样", len(rows),
        "<" if degenerate else "≥", a.min_rows))
    print("池大小：%d 颗（氨基酸 %d 颗＋蛋白质 %d 颗，--exclude 移除 %d 颗%s）" % (
        len(pool), len(folders), len(protein_names), len(excluded),
        "：" + "、".join(excluded) if excluded else ""))

    print("\n【逐行解析审计】")
    for i, date, sess, drawn, presented, verdict in audit:
        print("  第 %2d 行 %s │ %s" % (i, date, sess))
        if drawn is None:
            print("           〔非抽样行，跳过权重统计〕")
            continue
        silent = [f for f in drawn if f not in presented]
        print("           抽中：%s" % ("｜".join(drawn) or "（无）"))
        print("           呈现：%s" % ("｜".join(presented) or "（无）"))
        print("           静默：%s" % ("｜".join(silent) or "（无）"))
        print("           裁定：%s" % (verdict or "（空）"))

    print("\n【告警区】")
    if notes:
        seen = {}
        for lvl, msg, r in notes:
            seen.setdefault((lvl, msg), []).append(r)
        for (lvl, msg), rs in seen.items():
            rs = [x for x in rs if x is not None]
            tail = "（第 %s 数据行）" % "、".join(str(x) for x in rs) if rs else ""
            print("  〔%s〕%s%s" % (lvl, msg, tail))
    else:
        print("  （无）")

    print("\n【权重表】%s" % ("（退化模式下不参与抽样，仅供参考）" if degenerate else ""))
    total = sum(wt[f][3] for f in pool) or 1.0
    w0 = max([dw(f) for f in pool] + [dw("卡名")])
    print("  " + pad("卡名", w0) + "  赫布  蔡格尼克   衰减  最终权重  权重占比")
    print("  " + "─" * (w0 + 42))
    for f in sorted(pool, key=lambda x: (-wt[x][3], x)):
        h, z, d, w = wt[f]
        tail = []
        if streak[f]:
            tail.append("streak=%d" % streak[f])
        if f in pbase:
            tail.append("蛋白质·基线=成员最大%.2f" % pbase[f])
        print("  %s  ×%.1f     ×%.1f   ×%.2f     %5.2f    %5.1f%%  %s" % (
            pad(f, w0), h, z, d, w, w / total * 100, " ".join(tail)))

    # ── 抽样 ────────────────────────────────────────────────────
    print("\n【抽取结果】n=%d" % n)
    picks = []

    def family_of(f):
        # 2026-08-10 语义澄清：只禁「蛋白质×自家成员」同出（冗余抽取）；
        # 成员相互之间不受限——簇内成员碰撞是 M4 活文档的生长来源，不得扼杀。
        out = set()
        for pn, mem in proteins.items():
            if f == pn:
                out |= set(mem)
            elif f in mem:
                out.add(pn)
        out.discard(f)
        return out

    if len(pool) <= n:
        print("  〔提示〕池大小 %d ≤ n=%d，全取（同族去重不适用）" % (len(pool), n))
        picks = [(f, "全取") for f in sorted(pool)]
    else:
        chosen, blocked = set(), set()

        def take(slot):
            nonlocal blocked
            cand = [f for f in sorted(pool) if f not in chosen and f not in blocked]
            if not cand:
                print("  〔同族去重〕候选耗尽，本次仅抽出 %d 颗" % len(picks))
                return False
            if slot in ("野卡", "均匀"):
                f = cand[rng.randrange(len(cand))]
            else:
                f = cand[weighted_pop(cand, [wt[x][3] for x in cand], rng)]
            chosen.add(f)
            fam = family_of(f)
            let = sorted(x for x in fam if x in pool and x not in chosen and x not in blocked)
            if let:
                print("  〔同族去重〕「%s」入选，其同族本次让位：%s" % (f, "、".join(let)))
            blocked |= fam
            picks.append((f, slot))
            return True

        if degenerate:
            for _ in range(n):
                if not take("均匀"):
                    break
        else:
            if take("野卡"):
                for _ in range(n - 1):
                    if not take("加权"):
                        break

    for k, (f, slot) in enumerate(picks, 1):
        print("  %d. 〔%s〕%s   权重 %.2f（占比 %.1f%%）" % (k, slot, f, wt[f][3], wt[f][3] / total * 100))
        print("     %s" % cards[f])
    return 0


if __name__ == "__main__":
    sys.exit(main())
