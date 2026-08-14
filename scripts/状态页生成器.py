#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 状态页生成器：读取原始汤 INDEX.md / 闪电台账.md / 各文件夹氨基酸卡，
# 生成内嵌数据的静态状态页（预生成式——生成时快照数据，2026-08-08 定）。
# 用法：py 状态页生成器.py <原始汤根目录> [输出html路径] [--stamp "YYYY-MM-DD HH:MM"|fixed]
# 约定：每次原始汤会话归档或潮汐周任务运行时重建（落盘 _氨基酸库\状态页.html 浏览器查看）。
# ── 通用改造版── 默认行为与原版一致；新增：
#    R1 入口预检：_氨基酸库\INDEX.md 与 _氨基酸库\闪电台账.md 缺失时友好报错并退出码 1，
#      替代原版的 FileNotFoundError traceback（移植发现 1b）；
#    R4 --stamp：固定时间戳注入（--stamp "YYYY-MM-DD HH:MM"；--stamp fixed 简写 = 2026-08-30 09:00），
#      缺省=now 保持原行为，供确定性重建与快照比对（移植发现 8）；
#    R6 编码口径：stdout/stderr reconfigure utf-8；读文件统一 utf-8-sig（原为 utf-8；移植发现 13c/13e）。
import sys, json, glob, os, datetime

# R6：stdout/stderr 强制 UTF-8（Windows cmd 重定向默认本地编码，中文会乱码）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# R4：--stamp 固定时间戳（缺省=now 保持原行为；--stamp fixed 简写为固定值）
FIXED_STAMP = "2026-08-30 09:00"

def _parse_args(argv):
    positionals = []
    stamp = None
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--stamp":
            if i + 1 >= len(argv):
                sys.stderr.write("错误：--stamp 需要值（用法：--stamp \"YYYY-MM-DD HH:MM\" 或 --stamp fixed）\n")
                sys.exit(1)
            stamp = argv[i + 1]
            i += 2
        elif a.startswith("--stamp="):
            stamp = a[len("--stamp="):]
            i += 1
        else:
            positionals.append(a)
            i += 1
    root = positionals[0] if len(positionals) > 0 else "."
    out_path = positionals[1] if len(positionals) > 1 else os.path.join(root, "_氨基酸库", "状态页.html")
    if stamp is None:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    elif stamp == "fixed":
        stamp = FIXED_STAMP
    return root, out_path, stamp

root, out_path, stamp = _parse_args(sys.argv)

def read(p):
    with open(p, encoding="utf-8-sig") as f:  # R6：原 utf-8，统一 utf-8-sig（防 BOM 被当正文）
        return f.read()

# R1：入口预检——root 下 _氨基酸库\INDEX.md 与 _氨基酸库\闪电台账.md 必须存在，
# 缺失时友好报错并退出码 1（替代原版的 FileNotFoundError traceback）
_required = ["INDEX.md", "闪电台账.md"]
_missing = [name for name in _required
            if not os.path.isfile(os.path.join(root, "_氨基酸库", name))]
if _missing:
    for name in _missing:
        rel = os.path.join("_氨基酸库", name)
        sys.stderr.write("错误：未找到 %s（期望路径 %s）\n" % (rel, os.path.abspath(os.path.join(root, "_氨基酸库", name))))
    sys.exit(1)

index_md = read(os.path.join(root, "_氨基酸库", "INDEX.md"))
ledger_md = read(os.path.join(root, "_氨基酸库", "闪电台账.md"))

t = c = 0
open_items = []  # (文件夹名, 条目文本)
for p in sorted(glob.glob(os.path.join(root, "*", "_氨基酸.md"))):
    folder_name = os.path.basename(os.path.dirname(p))
    inq = False
    for line in read(p).splitlines():
        if line.startswith("## 未解问题"):
            inq = True
            continue
        if line.startswith("## "):
            inq = False
        if inq and line.startswith("- "):
            t += 1
            if "已由" in line or "已被" in line:
                c += 1
            else:
                open_items.append((folder_name, line[2:].strip()))

openqlist_txt = "\n".join(f + "\t" + item for f, item in open_items)

# 产出分类统计
n_protein = len(glob.glob(os.path.join(root, "_氨基酸库", "蛋白质：*.md")))
n_ticket = len(glob.glob(os.path.join(root, "*", "工单：*.md")))
n_article = len(glob.glob(os.path.join(root, "*", "文章：*.md")))
skills_dir = os.path.join(root, ".agents", "skills")
n_skill = len([d for d in glob.glob(os.path.join(skills_dir, "*")) if os.path.isdir(d)]) if os.path.isdir(skills_dir) else 0
outputs_json = json.dumps(
    {"蛋白质": n_protein, "工单": n_ticket, "文章": n_article, "skill": n_skill},
    ensure_ascii=False,
)

products_path = os.path.join(root, "_氨基酸库", "产品台账.md")
products_md = read(products_path) if os.path.exists(products_path) else ""

raw = (
    "===INDEX===\n" + index_md
    + "\n===PRODUCTS===\n" + products_md
    + "\n===LEDGER===\n" + ledger_md
    + "\n===OPENQ===\n" + str(t) + " " + str(c)
    + "\n===OPENQLIST===\n" + openqlist_txt
    + "\n===OUTPUTS===\n" + outputs_json
)
# R4：stamp 已在 _parse_args 中解析（缺省=now；--stamp 固定值；--stamp fixed 简写 = FIXED_STAMP）

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>原始汤 · 状态仪表盘</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Segoe UI", "Microsoft YaHei", system-ui, sans-serif; background: #faf8f4; color: #2b2b2b; padding: 20px; font-size: 14px; }
  h1 { font-size: 19px; margin-bottom: 4px; }
  .sub { color: #8a8377; font-size: 12px; margin-bottom: 18px; }
  h2 { font-size: 14px; margin: 22px 0 10px; color: #5a5348; border-bottom: 1px solid #e8e2d8; padding-bottom: 5px; }
  .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; }
  .kpi { background: #fff; border: 1px solid #e8e2d8; border-radius: 10px; padding: 12px 14px; }
  .kpi .num { font-size: 24px; font-weight: 700; color: #7a5c2e; }
  .kpi .lbl { font-size: 12px; color: #8a8377; margin-top: 2px; }
  .bars { display: grid; gap: 10px; }
  .bar-row { background: #fff; border: 1px solid #e8e2d8; border-radius: 10px; padding: 10px 14px; }
  .bar-head { display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 6px; gap: 12px; }
  .bar-track { background: #efe9df; border-radius: 6px; height: 8px; overflow: hidden; }
  .bar-fill { background: #b08b4f; height: 100%; border-radius: 6px; }
  .bar-fill.hot { background: #c25e3a; }
  table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #e8e2d8; border-radius: 10px; overflow: hidden; }
  th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid #f0ebe2; vertical-align: top; }
  th { background: #f4efe7; font-size: 12px; color: #6b6357; white-space: nowrap; }
  td { font-size: 12.5px; line-height: 1.5; }
  tr:last-child td { border-bottom: none; }
  .pill { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 11.5px; white-space: nowrap; }
  .p-ok { background: #e3efdd; color: #3d6b2f; }
  .p-wait { background: #f5ead2; color: #8a6a24; }
  .p-no { background: #f3ddd6; color: #9c3f22; }
  .p-meh { background: #e8e5e0; color: #6b6357; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; }
  .tag { background: #fff; border: 1px solid #e0d8c9; border-radius: 999px; padding: 3px 10px; font-size: 12px; color: #5a5348; }
  .tag b { color: #7a5c2e; }
  .tag.dom { background: #f2f5ef; border-color: #cfdac4; color: #47603a; }
  .tag.dom b { color: #3d6b2f; }
  .p-cat { background: #eee8f0; color: #5d4a6b; }
  .cnt { font-size: 12px; color: #a09a8e; font-weight: 400; }
  td.nw { white-space: nowrap; color: #8a8377; font-size: 12px; }
  td.prog { background: #fdfaf4; }
  .idea { background: #fff; border: 1px solid #e8e2d8; border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; }
  .idea-t { font-size: 13px; font-weight: 700; color: #5a5348; margin-bottom: 4px; }
  .idea-d { font-size: 12.5px; line-height: 1.65; color: #4a453d; }
  .gloss { display: block; font-size: 10.5px; color: #b0a89a; font-weight: 400; margin-top: 1px; letter-spacing: 0; }
  th.sortable { cursor: pointer; user-select: none; position: relative; padding-right: 18px; }
  th.sortable:hover { background: #ece5d9; }
  th.sortable::after { content: "⇅"; position: absolute; right: 6px; color: #c3bbab; font-size: 10px; }
  th.sortable.asc::after { content: "↑"; color: #7a5c2e; }
  th.sortable.desc::after { content: "↓"; color: #7a5c2e; }
  .err { background: #fdf0ec; border: 1px solid #eec7ba; color: #8c3a1e; padding: 14px; border-radius: 10px; line-height: 1.6; word-break: break-all; }
  .foot { margin-top: 20px; font-size: 11.5px; color: #a09a8e; line-height: 1.6; }
  details.openq { background: #fff; border: 1px solid #e8e2d8; border-radius: 10px; padding: 8px 14px; margin-bottom: 8px; }
  details.openq summary { cursor: pointer; font-size: 12.5px; color: #5a5348; }
  details.openq summary::marker { color: #b08b4f; }
  details.openq ul { margin: 8px 0 4px 18px; }
  details.openq li { font-size: 12.5px; line-height: 1.6; margin-bottom: 4px; color: #4a453d; }
  .section-foot { margin-top: 10px; font-size: 11.5px; color: #a09a8e; line-height: 1.6; }
</style>
</head>
<body>
<h1>原始汤 · 状态仪表盘</h1>
<div class="sub">数据截至 __STAMP__ · 由原始汤会话归档或潮汐重建时刷新（预生成式）</div>
<div id="app"></div>
<div class="foot">数据源：_氨基酸库/INDEX.md 与 闪电台账.md。M4 簇判定属人工/潮汐职责，不在本页自动计算。抽样权重口径见 闪电抽样器.py 输出（含逐行解析审计）。重建方式：运行 _氨基酸库/状态页生成器.py 后刷新页面。</div>
<script>
const RAW = __RAW__;
const M5_DEADLINE = new Date("2026-11-12T00:00:00");
const M5_START = new Date("2026-08-08T00:00:00");

function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function cut(s,n){ s=String(s); return s.length>n ? s.slice(0,n)+"…" : s; }
function parseTable(txt){
  const rows = txt.split("\n").filter(l=>l.trim().startsWith("|"))
    .map(l=>l.split("|").slice(1,-1).map(c=>c.trim()));
  return rows.filter(r=>!/^[-:\s]*$/.test(r.join(""))).slice(1);
}
// 表格排序：点表头升序、再点降序、第三次回到原始顺序。数字按数值比，其余按中文本地化字典序。
function makeSortable(){
  document.querySelectorAll("table").forEach(tb=>{
    const body = tb.tBodies[0]; if(!body) return;
    const rows = Array.from(body.rows); if(rows.length < 3) return;
    const head = rows[0], data = rows.slice(1);
    data.forEach((r,i)=>r.dataset.ord = i);
    Array.from(head.cells).forEach((th,ci)=>{
      th.classList.add("sortable");
      th.title = "点击排序";
      th.addEventListener("click", ()=>{
        const cur = th.classList.contains("asc") ? "asc" : th.classList.contains("desc") ? "desc" : "";
        const next = cur === "" ? "asc" : cur === "asc" ? "desc" : "";
        Array.from(head.cells).forEach(c=>c.classList.remove("asc","desc"));
        if(next) th.classList.add(next);
        const val = r => (r.cells[ci] ? r.cells[ci].textContent.trim() : "");
        const num = s => { const m = s.replace(/[^0-9.\-]/g,""); return m === "" ? null : parseFloat(m); };
        const sorted = data.slice().sort((a,b)=>{
          if(!next) return (+a.dataset.ord) - (+b.dataset.ord);
          const x = val(a), y = val(b);
          const nx = num(x), ny = num(y);
          let c;
          if(nx !== null && ny !== null && !isNaN(nx) && !isNaN(ny) && x.length < 14 && y.length < 14) c = nx - ny;
          else c = x.localeCompare(y, "zh-Hans-CN");
          return next === "asc" ? c : -c;
        });
        sorted.forEach(r=>body.appendChild(r));
      });
    });
  });
}
function verdictPill(v){
  if(v.includes("认可")) return '<span class="pill p-ok">'+esc(v)+'</span>';
  if(v.includes("反对")) return '<span class="pill p-no">'+esc(v)+'</span>';
  if(v.includes("无感")) return '<span class="pill p-meh">'+esc(v)+'</span>';
  return '<span class="pill p-wait">'+esc(v||"待补")+'</span>';
}
function bar(label, val, target, rightText){
  const pct = target > 0 ? Math.min(100, Math.round(val/target*100)) : 0;
  return '<div class="bar-row"><div class="bar-head"><span>'+label+'</span><span>'+(rightText!==undefined?rightText:(val+' / '+target+(pct>=100?'（已达标）':'')))+'</span></div><div class="bar-track"><div class="bar-fill'+(pct>=100?' hot':'')+'" style="width:'+pct+'%"></div></div></div>';
}
function main(){
  try{
    const out = RAW;
    const idx  = parseTable(out.split("===INDEX===")[1].split("===PRODUCTS===")[0]);
    const prodRaw = (out.split("===PRODUCTS===")[1]||"").split("===LEDGER===")[0];
    const prodSec = n => { const m = prodRaw.split("\n## "); const s = m.find(x=>x.startsWith(n)); return s ? parseTable(s) : []; };
    const prodDone = prodSec("已完成"), prodWip = prodSec("待完成"), prodIdea = prodSec("早期设想");
    const led  = parseTable(out.split("===LEDGER===")[1].split("===OPENQ===")[0]);
    const oq   = (out.split("===OPENQ===")[1].split("===OPENQLIST===")[0]||"").trim().split(/\s+/);
    const oqTotal = parseInt(oq[0]||"0") || 0, oqClosed = parseInt(oq[1]||"0") || 0;
    const oqListRaw = out.split("===OPENQLIST===")[1].split("===OUTPUTS===")[0];
    const oqList = oqListRaw.split("\n").map(l=>l.replace(/\r$/,"")).filter(l=>l.length>0)
      .map(l=>{ const i=l.indexOf("\t"); return i>=0 ? [l.slice(0,i), l.slice(i+1)] : [l, ""]; });
    const outputsRaw = out.split("===OUTPUTS===")[1] || "{}";
    const outputs = JSON.parse(outputsRaw.trim() || "{}");

    const presented = led.filter(r=>(r[3]||"").startsWith("是"));
    const nOK   = led.filter(r=>(r[4]||"").includes("认可")).length;
    const nNo   = led.filter(r=>(r[4]||"").includes("反对")).length;
    const nMeh  = led.filter(r=>(r[4]||"").includes("无感")).length;
    const pend  = led.filter(r=>(r[3]||"").startsWith("是") && (r[4]||"").includes("待补"));

    const now = new Date();
    const daysLeft = Math.max(0, Math.ceil((M5_DEADLINE - now) / 86400000));
    const totalDays = Math.round((M5_DEADLINE - M5_START) / 86400000);
    const elapsed = Math.min(totalDays, Math.max(0, totalDays - daysLeft));

    const tagCount = {};
    idx.forEach(r=>(r[4]||"").split(/\s+/).forEach(t=>{ if(t.startsWith("#")) tagCount[t]=(tagCount[t]||0)+1; }));
    const topTags = Object.entries(tagCount).sort((a,b)=>b[1]-a[1]).slice(0,14);

    const domCount = {};
    let domCards = 0;
    idx.forEach(r=>{
      const ds = (r[4]||"").split(/\s+/).filter(t=>t.startsWith("@"));
      if(ds.length) domCards++;
      ds.forEach(t=>domCount[t]=(domCount[t]||0)+1);
    });
    const domTags = Object.entries(domCount).sort((a,b)=>b[1]-a[1]);

    let h = "";
    h += '<div class="kpis">'
      + '<div class="kpi"><div class="num">'+idx.length+'</div><div class="lbl">氨基酸<span class="gloss">一次讨论的结论卡</span></div></div>'
      + '<div class="kpi"><div class="num">'+led.length+'</div><div class="lbl">闪电抽取<span class="gloss">随机翻出旧卡撞今天的话题</span></div></div>'
      + '<div class="kpi"><div class="num">'+presented.length+'</div><div class="lbl">碰撞呈现</div></div>'
      + '<div class="kpi"><div class="num">'+nOK+'</div><div class="lbl">裁定认可</div></div>'
      + '<div class="kpi"><div class="num">'+pend.length+'</div><div class="lbl">待裁定</div></div>'
      + '<div class="kpi"><div class="num">'+(oqTotal-oqClosed)+'<span style="font-size:13px;color:#a09a8e"> / '+oqTotal+'</span></div><div class="lbl">未解问题 开放/总</div></div>'
      + '</div>'
      + '<div class="section-foot">口径：闪电抽取＝台账数据行（含静默与非抽样行）；碰撞呈现＝『是否呈现』以「是」开头的行；待裁定＝已呈现且裁定为「待补」。</div>';

    const folderTypeCount = {};
    idx.forEach(r=>{
      const folder = r[2]||"";
      const ci = folder.indexOf("：");
      const prefix = ci >= 0 ? folder.slice(0, ci) : "其他";
      folderTypeCount[prefix] = (folderTypeCount[prefix]||0) + 1;
    });
    const folderTypeOrder = ["机制","讨论","研究","产品"];
    const folderTypeEntries = Object.entries(folderTypeCount).sort((a,b)=>{
      const ai = folderTypeOrder.indexOf(a[0]), bi = folderTypeOrder.indexOf(b[0]);
      if(ai === -1 && bi === -1) return b[1]-a[1];
      if(ai === -1) return 1;
      if(bi === -1) return -1;
      return ai - bi;
    });

    h += '<h2>产出分类</h2><div class="kpis">'
      + '<div class="kpi"><div class="num">'+(outputs["蛋白质"]||0)+'</div><div class="lbl">蛋白质<span class="gloss">多张卡合成的综述</span></div></div>'
      + '<div class="kpi"><div class="num">—</div><div class="lbl">标准</div></div>'
      + '<div class="kpi"><div class="num">'+(outputs["文章"]||0)+'</div><div class="lbl">文章</div></div>'
      + '<div class="kpi"><div class="num">'+(outputs["工单"]||0)+'</div><div class="lbl">工单</div></div>'
      + '<div class="kpi"><div class="num">'+(outputs["skill"]||0)+'</div><div class="lbl">skill</div></div>'
      + '</div>'
      + '<div class="tags" style="margin-top:10px">'
      + folderTypeEntries.map(([k,v])=>'<span class="tag">'+esc(k)+' <b>'+v+'</b></span>').join("")
      + '</div>'
      + '<div class="section-foot">标准类暂无正式标签约定（#公理 待定）；文章按 文章：*.md 命名约定统计；类型徽章按 INDEX『文件夹』列前缀统计；氨基酸总数见顶部，不重复列示。</div>';

    const catPill = c => '<span class="pill p-cat">'+esc(c)+'</span>';
    h += '<h2>产品视图 · 已完成 <span class="cnt">'+prodDone.length+'</span></h2>'
      + '<table><tr><th>产品</th><th>类别</th><th>日期</th><th>概述</th></tr>'
      + prodDone.slice().reverse().map(r=>'<tr><td><b>'+esc(r[0])+'</b></td><td>'+catPill(r[1])+'</td><td class="nw">'+esc(r[2])+'</td><td>'+esc(r[3])+'</td></tr>').join("")
      + '</table>'
      + '<div class="section-foot">口径：东西在盘上、能交付、不再需要动作。新→旧排列。数据源 _氨基酸库/产品台账.md。</div>';

    h += '<h2>产品视图 · 待完成 <span class="cnt">'+prodWip.length+'</span></h2>'
      + '<table><tr><th>产品</th><th>类别</th><th>日期</th><th>概述</th><th>当前进度</th></tr>'
      + prodWip.map(r=>'<tr><td><b>'+esc(r[0])+'</b></td><td>'+catPill(r[1])+'</td><td class="nw">'+esc(r[2])+'</td><td>'+esc(r[3])+'</td><td class="prog">'+esc(r[4])+'</td></tr>').join("")
      + '</table>'
      + '<div class="section-foot">口径：已立项或已开单、有明确下一步动作。「当前进度」写卡在哪一步，不写百分比——百分比是自评，卡点是事实。</div>';

    h += '<h2>早期设想 <span class="cnt">'+prodIdea.length+'</span></h2>'
      + prodIdea.map(r=>'<div class="idea"><div class="idea-t">'+esc(r[0])+'</div><div class="idea-d">'+esc(r[1])+'</div></div>').join("")
      + '<div class="section-foot">口径：只在讨论里成过形，既没立项也没否决。和上面两张表分开放，是为了让「已承诺的事」与「想过的事」不互相稀释。</div>';

    h += '<h2>机制哨兵（M3–M5 触发进度）</h2><div class="bars">'
      + '<div class="bar-row"><div class="bar-head"><span>M3 加权抽样：已构建（2026-08-09）· 闪电抽样器.py 运行中</span><span>权重数据 '+led.length+' 行</span></div><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div></div>'
      + bar("M5 结算：氨基酸颗数", idx.length, 50)
      + bar("M5 结算：时间闸门（2026-11-12 到期）", elapsed, totalDays, daysLeft > 0 ? "剩余 "+daysLeft+" 天" : "已到期")
      + '<div class="bar-row"><div class="bar-head"><span>M4 蛋白质合成：簇判定属潮汐/人工，本页不自动计算</span><span>碰撞裁定供给：认可 '+nOK+' · 无感 '+nMeh+' · 反对 '+nNo+'</span></div></div>'
      + '</div>'
      + '<div class="section-foot">M3 已构建，此行是状态标注非触发进度；M4 簇判定见最新潮汐周报；M5 双闸门（50 颗或 2026-11-12）先到为准，结算时两硬指标（未解问题关闭数、碰撞改变结论数）均为零则闪电降级为手动。</div>';

    if (pend.length){
      h += '<h2>待裁定（'+pend.length+'）</h2><table><tr><th>日期</th><th>会话</th><th>备注</th></tr>'
        + pend.map(r=>'<tr><td>'+esc(r[0])+'</td><td>'+esc(cut(r[1],28))+'</td><td>'+esc(cut(r[5],80))+'</td></tr>').join("")
        + '</table>'
        + '<div class="section-foot">仅呈现过碰撞的行需要裁定；本表不出现即无欠账。</div>';
    }

    const openqByFolder = {};
    oqList.forEach(([folder,item])=>{
      if(!openqByFolder[folder]) openqByFolder[folder] = [];
      openqByFolder[folder].push(item);
    });
    const openqGroups = Object.entries(openqByFolder).sort((a,b)=>b[1].length-a[1].length);

    h += '<h2>开放的未解问题（'+oqList.length+'）</h2>'
      + openqGroups.map(([folder,items])=>
          '<details class="openq"><summary>'+esc(folder)+'（'+items.length+' 条）</summary><ul>'
          + items.map(it=>'<li>'+esc(cut(it,160))+'</li>').join("")
          + '</ul></details>'
        ).join("")
      + '<div class="section-foot">关闭＝条目内有「已由/已被」回写（M2 机制）；未解问题关闭数是 M5 的北极星指标。</div>';

    h += '<h2>最近闪电（新→旧）</h2><table><tr><th>日期</th><th>会话</th><th>裁定</th><th>备注</th></tr>'
      + led.slice(-6).reverse().map(r=>'<tr><td>'+esc(r[0])+'</td><td>'+esc(cut(r[1],26))+'</td><td>'+verdictPill(r[4]||"")+'</td><td>'+esc(cut(r[5],90))+'</td></tr>').join("")
      + '</table>'
      + '<div class="section-foot">每行＝一次抽取事件，被静默的抽取也登记（沉默可审计）；完整历史见 闪电台账.md。</div>';

    h += '<h2>氨基酸总表（新→旧）</h2><table><tr><th>编号</th><th>日期</th><th>文件夹</th><th>一句话结论</th></tr>'
      + idx.slice().reverse().map(r=>'<tr><td>'+esc(r[0])+'</td><td>'+esc(r[1])+'</td><td>'+esc(cut(r[2],24))+'</td><td>'+esc(cut(r[5],96))+'</td></tr>').join("")
      + '</table>'
      + '<div class="section-foot">INDEX.md 的镜像视图；检索一律以 INDEX 为唯一入口。编号按登记顺序发放、一经发出不变，注销卡的号作废不复用；文件夹名仍是全库主键，编号是别名。</div>';

    h += '<h2>标签分布</h2><div class="tags">'
      + topTags.map(([t,c])=>'<span class="tag">'+esc(t)+' <b>'+c+'</b></span>').join("")
      + '</div>'
      + '<div class="section-foot">统计 INDEX『标签』列里 # 开头的方法维标签；与『产出分类』的文件夹前缀徽章是两套维度。</div>';

    h += '<h2>借力知识领域</h2><div class="tags">'
      + (domTags.length ? domTags.map(([t,c])=>'<span class="tag dom">'+esc(t)+' <b>'+c+'</b></span>').join("")
                        : '<span class="tag dom">暂无标注</span>')
      + '</div>'
      + '<div class="section-foot">口径：@ 标的是这张卡的论证从哪个外部知识领域借了框架、隐喻、证据或方法，不标 AI／知识管理等本域；一卡 0–3 个，允许为空。'
      + '当前 '+domCards+' / '+idx.length+' 张卡有标注，'+(idx.length-domCards)+' 张判空（未借外部领域）。跨领域是闪电碰撞的高产区。</div>';

    document.getElementById("app").innerHTML = h;
    makeSortable();
  }catch(e){
    document.getElementById("app").innerHTML = '<div class="err">状态页渲染失败：'+esc(e.message)+'——请重新运行 状态页生成器.py 生成本页。</div>';
  }
}
main();
</script>
</body>
</html>
'''

html = TEMPLATE.replace("__RAW__", json.dumps(raw, ensure_ascii=False)).replace("__STAMP__", stamp)
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", out_path)
