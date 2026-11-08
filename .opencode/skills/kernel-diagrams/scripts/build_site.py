#!/usr/bin/env python3
"""构建 Archify 图表画廊首页(Blueprint Console 版)。

扫描候选目录下的 */candidate.json,读取 diagram_type / meta.title / meta.output,
生成站点首页 index.html:分类导轨 + 搜索/类型筛选 + 分区网格 + 终端窗口卡片。

用法:
  python3 build_site.py [候选目录] [站点目录] [--title 站点标题]

默认:候选目录 .archify,站点目录 site。
仅用 python3 标准库。
"""
import argparse
import html
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

TYPE_LABELS = {
    "architecture": "架构图",
    "workflow": "流程图",
    "sequence": "时序图",
    "dataflow": "数据流",
    "lifecycle": "状态机",
    "erd": "ER 图",
    "class": "类图",
    "tree": "树形图",
    "timeline": "时间线",
    "waterfall": "瀑布图",
}

CATEGORY_ORDER = [
    "内核总览", "进程管理", "内存管理", "网络协议栈", "文件系统",
    "设备驱动", "NVMe驱动", "内核驱动框架", "存储技术", "并发与同步",
]

CATEGORY_DESC = {
    "内核总览": "子系统全景",
    "进程管理": "调度 / 创建 / 信号 / 退出",
    "内存管理": "缺页 / 分配器 / 回收",
    "网络协议栈": "TCP/IP / NAPI / epoll",
    "文件系统": "VFS / ext4 / 写回",
    "设备驱动": "驱动模型 / 块 IO",
    "NVMe驱动": "队列 / 门铃 / IO 路径",
    "内核驱动框架": "bus/device/driver / devres",
    "存储技术": "异步 IO",
    "并发与同步": "RCU / 锁 / per-CPU",
}


def read_mmd_description(site_item):
    """可选:从遗留 .mmd 的 frontmatter 读取描述(仅用于迁移期补充说明)。"""
    project = Path(".")
    mmd = project / "diagrams" / site_item["category"] / (site_item["slug"] + ".mmd")
    if not mmd.is_file():
        return ""
    text = mmd.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        if line.strip().startswith("description:"):
            return line.split(":", 1)[1].strip()
    return ""


def collect(candidates_dir, site_dir):
    base = Path(candidates_dir)
    if not base.is_dir():
        sys.exit(f"错误:候选目录不存在: {base}")
    items = []
    seen = set()
    for cand in sorted(base.glob("*/candidate.json")):
        try:
            data = json.loads(cand.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"跳过无法解析的 {cand}: {e}", file=sys.stderr)
            continue
        meta = data.get("meta", {})
        output = meta.get("output")
        dtype = data.get("diagram_type") or ""
        if not output:
            print(f"跳过缺少 meta.output 的 {cand}", file=sys.stderr)
            continue
        out_path = Path(output)
        if not out_path.is_file():
            print(f"跳过尚未生成的产物 {output}(候选 {cand})", file=sys.stderr)
            continue
        if output in seen:
            continue
        seen.add(output)
        try:
            rel = out_path.relative_to(Path(site_dir))
        except ValueError:
            print(f"跳过站点目录之外的产物 {output}", file=sys.stderr)
            continue
        parts = rel.parts
        category = parts[0] if len(parts) > 1 else "未分类"
        slug = out_path.stem
        item = {
            "title": meta.get("title") or slug,
            "subtitle": meta.get("subtitle") or "",
            "type": dtype or (cand.parent.name.split("-", 1)[0]),
            "output": output,
            "rel": str(rel),
            "category": category,
            "slug": slug,
        }
        if not item["subtitle"]:
            item["subtitle"] = read_mmd_description(item)
        items.append(item)
    return items


def build_page(items, title):
    cats = OrderedDict()
    for it in items:
        cats.setdefault(it["category"], []).append(it)

    ordered = [c for c in CATEGORY_ORDER if c in cats]
    ordered += [c for c in cats if c not in ordered]
    deep_count = sum(1 for it in items if it["slug"].startswith("deep-"))

    type_present = OrderedDict()
    for it in items:
        type_present.setdefault(it["type"], TYPE_LABELS.get(it["type"], it["type"]))

    # 卡片按分类分组
    section_html = []
    for idx, cat in enumerate(ordered):
        arr = cats[cat]
        cards = []
        for it in arr:
            label = TYPE_LABELS.get(it["type"], it["type"])
            desc = it["subtitle"] or f"{label} · 点击打开交互细节"
            searchable = f'{it["title"]} {desc} {it["category"]} {it["type"]}'.lower()
            is_deep = it["slug"].startswith("deep-")
            deep_attr = ' data-deep="1"' if is_deep else ""
            deep_badge = '<span class="deep-badge">DEEP</span>' if is_deep else ""
            cards.append(f'''
        <article class="card" data-type="{html.escape(it['type'])}"
                 data-category="{html.escape(it['category'])}"
                 data-search="{html.escape(searchable)}"{deep_attr}>
          <div class="win-bar">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            <span class="win-path">{html.escape(it["category"])}/{html.escape(it["slug"])}</span>
            {deep_badge}
            <span class="badge t-{html.escape(it['type'])}">{html.escape(label)}</span>
          </div>
          <div class="win-body">
            <h3>{html.escape(it["title"])}</h3>
            <p>{html.escape(desc)}</p>
            <div class="preview">
              <iframe src="{html.escape(it['rel'])}" loading="lazy" title="{html.escape(it['title'])}"></iframe>
            </div>
          </div>
          <div class="win-foot">
            <span>{html.escape(it["category"])}</span>
            <a href="{html.escape(it['rel'])}" target="_blank" rel="noopener">打开交互图 ↗</a>
          </div>
        </article>''')
        sub = CATEGORY_DESC.get(cat, "")
        section_html.append(f'''
      <section class="cat-sec" id="cat-{idx}" data-cat="{html.escape(cat)}">
        <div class="cat-head">
          <span class="cat-num">{idx + 1:02d}</span>
          <h2>{html.escape(cat)}</h2>
          <span class="cat-sub">{html.escape(sub)}</span>
          <span class="cat-count">{len(arr)}</span>
          <span class="rule"></span>
        </div>
        <div class="grid">{''.join(cards)}</div>
      </section>''')

    cat_nav = [f'<button class="cat-btn active" data-cat="all" data-target="">全部 <span class="n">{len(items)}</span></button>']
    for idx, cat in enumerate(ordered):
        cat_nav.append(
            f'<button class="cat-btn" data-cat="{html.escape(cat)}" data-target="cat-{idx}">'
            f'{html.escape(cat)} <span class="n">{len(cats[cat])}</span></button>'
        )

    chips = ['<button class="chip active" data-type="all">全部</button>']
    for t, label in type_present.items():
        chips.append(f'<button class="chip" data-type="{html.escape(t)}">{html.escape(label)}</button>')

    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<style>
:root {
  --bg:#0f172a; --bg2:#13203a; --panel:#16233b; --card:#182741;
  --border:#2b3d5c; --border2:#3f5878; --text:#eef4ff; --muted:#a6b6cf;
  --emerald:#3ddc97; --cyan:#38bdf8; --amber:#fbbf24; --violet:#a78bfa;
  --grad:linear-gradient(120deg,#34d399,#22d3ee 55%,#60a5fa);
  --mono:ui-monospace,"SFMono-Regular","JetBrains Mono",Consolas,monospace;
}
* { box-sizing:border-box; margin:0; padding:0; }
html { scroll-behavior:smooth; }
body {
  display:grid; grid-template-columns:286px minmax(0,1fr);
  min-height:100vh; background:var(--bg); color:var(--text);
  font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;
  background-image:
    radial-gradient(900px 520px at 10% -10%, rgba(52,211,153,.10), transparent 60%),
    radial-gradient(900px 520px at 96% 0%, rgba(34,211,238,.10), transparent 62%),
    linear-gradient(rgba(61,220,151,.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(61,220,151,.05) 1px, transparent 1px);
  background-size:auto, auto, 42px 42px, 42px 42px;
}
a { color:var(--emerald); text-decoration:none; }
a:hover { text-decoration:none; }

/* ===== rail ===== */
aside {
  position:sticky; top:0; height:100vh; overflow-y:auto;
  border-right:1px solid var(--border); background:rgba(15,23,42,.90);
  padding:20px 16px; backdrop-filter:blur(10px);
}
.brand { display:flex; align-items:center; gap:10px; color:var(--text); font-weight:800; letter-spacing:.02em; }
.brand-mark {
  width:30px; height:30px; border-radius:8px; background:var(--grad);
  color:#04120d; display:grid; place-items:center; font-weight:900; font-size:14px;
  box-shadow:0 8px 22px rgba(52,211,153,.25);
}
.brand small { display:block; color:var(--muted); font-family:var(--mono); font-size:10.5px; letter-spacing:.14em; font-weight:400; }
.aside-label { color:var(--muted); font-size:11px; letter-spacing:.16em; text-transform:uppercase; margin:20px 0 8px; font-family:var(--mono); }
#search {
  width:100%; padding:9px 12px; border-radius:8px; border:1px solid var(--border);
  background:var(--bg2); color:var(--text); font-size:13.5px; outline:none;
}
#search:focus { border-color:var(--emerald); box-shadow:0 0 0 2px rgba(52,211,153,.12); }
.chips { display:flex; flex-wrap:wrap; gap:6px; }
.chip {
  border:1px solid var(--border); background:var(--panel); color:var(--muted);
  padding:5px 11px; border-radius:999px; font-size:12.5px; cursor:pointer;
  transition:color .15s,border-color .15s,background .15s;
}
.chip:hover { color:var(--text); border-color:var(--border2); }
.chip.active { background:rgba(52,211,153,.14); border-color:rgba(52,211,153,.55); color:var(--emerald); }
.cat-nav { display:flex; flex-direction:column; gap:2px; }
.cat-btn {
  display:flex; align-items:center; justify-content:space-between; gap:8px;
  width:100%; text-align:left; background:none; border:1px solid transparent;
  border-left:2px solid transparent; color:var(--muted); cursor:pointer;
  padding:7px 9px; border-radius:0 6px 6px 0; font-size:14px;
  transition:color .15s,background .15s,border-color .15s;
}
.cat-btn:hover { color:var(--text); background:rgba(52,211,153,.06); }
.cat-btn.active { color:var(--emerald); border-left-color:var(--emerald); background:rgba(52,211,153,.08); }
.cat-btn .n { font-family:var(--mono); font-size:11.5px; color:var(--muted); }
.deep-toggle {
  width:100%; margin-top:10px; display:flex; align-items:center; justify-content:space-between;
  border:1px dashed var(--border2); background:rgba(251,191,36,.05); color:var(--muted);
  padding:8px 10px; border-radius:8px; font-size:12.5px; cursor:pointer;
}
.deep-toggle.active { color:var(--amber); border-color:rgba(251,191,36,.55); background:rgba(251,191,36,.10); }
.deep-toggle b { font-family:var(--mono); color:var(--amber); }
.rail-links { margin-top:16px; padding-top:12px; border-top:1px solid var(--border); display:flex; flex-direction:column; gap:5px; }
.rail-links a { color:var(--muted); font-size:13px; }
.rail-links a:hover { color:var(--emerald); }

/* ===== main ===== */
main { min-width:0; padding:30px clamp(20px,4vw,58px) 80px; }
.hero { padding:26px 0 30px; border-bottom:1px solid var(--border); }
.eyebrow { color:var(--muted); font-family:var(--mono); font-size:11px; letter-spacing:.18em; text-transform:uppercase; }
.eyebrow b { color:var(--emerald); font-weight:600; }
.hero h1 { font-size:clamp(1.9rem,3.6vw,3rem); line-height:1.15; margin:12px 0 10px; letter-spacing:-.02em; }
.hero h1 em { font-style:normal; background:var(--grad); -webkit-background-clip:text; background-clip:text; color:transparent; }
.lede { color:#c4d2e6; max-width:820px; font-size:14.5px; }
.hero-stats { display:flex; flex-wrap:wrap; gap:20px; margin-top:20px; color:var(--muted); font-size:12px; }
.hero-stats strong { color:var(--text); font-size:16px; margin-right:5px; font-family:var(--mono); }
.hero-actions { display:flex; flex-wrap:wrap; gap:10px; margin-top:20px; }
.btn {
  display:inline-flex; align-items:center; gap:6px; padding:8px 14px; border-radius:8px;
  font-size:12.5px; border:1px solid var(--border); color:var(--text); background:var(--panel);
}
.btn:hover { border-color:var(--border2); }
.btn.primary { background:var(--grad); color:#04120d; border-color:transparent; font-weight:700; }
.statusbar { display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin:16px 0 4px; color:var(--muted); font-size:12px; }
#stats { font-family:var(--mono); color:var(--emerald); }
#clear { margin-left:auto; background:none; border:none; color:var(--muted); cursor:pointer; font-size:12px; }
#clear:hover { color:var(--text); }

.cat-sec { padding:32px 0 6px; scroll-margin-top:20px; }
.cat-head { display:flex; align-items:baseline; gap:10px; margin-bottom:16px; }
.cat-num { font-family:var(--mono); font-size:11px; color:var(--emerald); }
.cat-head h2 { font-size:clamp(1.15rem,2vw,1.45rem); letter-spacing:-.01em; }
.cat-sub { color:var(--muted); font-size:12px; }
.cat-count { margin-left:auto; font-family:var(--mono); color:var(--muted); font-size:11px; }
.rule { flex:1; height:1px; background:linear-gradient(90deg,var(--border),transparent); margin-left:6px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(430px,1fr)); gap:16px; }

/* terminal-window card */
.card {
  border:1px solid var(--border); border-radius:11px; overflow:hidden;
  background:var(--card); min-width:0;
  transition:border-color .18s, transform .18s, box-shadow .18s;
}
.card:hover { border-color:rgba(52,211,153,.45); transform:translateY(-2px); box-shadow:0 18px 40px rgba(0,0,0,.35); }
.win-bar {
  display:flex; align-items:center; gap:6px; padding:8px 11px;
  border-bottom:1px solid var(--border); background:rgba(8,16,28,.9);
}
.win-bar .dot { width:8px; height:8px; border-radius:50%; background:#2a3d55; }
.win-bar .dot:nth-child(1) { background:#f87171; }
.win-bar .dot:nth-child(2) { background:#fbbf24; }
.win-bar .dot:nth-child(3) { background:#34d399; }
.win-path { margin-left:6px; font-family:var(--mono); font-size:10.5px; color:var(--muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.badge { margin-left:auto; font-size:10px; padding:2px 8px; border-radius:999px; white-space:nowrap; border:1px solid var(--border2); color:var(--muted); }
.t-architecture { color:#67e8f9; border-color:rgba(34,211,238,.45); background:rgba(34,211,238,.08); }
.t-workflow { color:#6ee7b7; border-color:rgba(52,211,153,.45); background:rgba(52,211,153,.08); }
.t-sequence { color:#c4b5fd; border-color:rgba(167,139,250,.45); background:rgba(167,139,250,.08); }
.t-lifecycle { color:#fcd34d; border-color:rgba(251,191,36,.45); background:rgba(251,191,36,.08); }
.t-tree { color:#f9a8d4; border-color:rgba(244,114,182,.4); background:rgba(244,114,182,.07); }
.deep-badge { font-size:9.5px; color:var(--amber); border:1px solid rgba(251,191,36,.5); background:rgba(251,191,36,.10); border-radius:4px; padding:1px 5px; font-family:var(--mono); }
.win-body { padding:12px 12px 10px; }
.win-body h3 { font-size:15px; letter-spacing:-.01em; }
.win-body p { color:var(--muted); font-size:12.5px; line-height:1.5; margin:5px 0 10px; min-height:36px; }
.preview { border:1px solid var(--border); border-radius:8px; overflow:hidden; background:var(--bg2); }
.preview iframe { width:100%; height:360px; border:0; display:block; }
.win-foot { display:flex; justify-content:space-between; align-items:center; padding:8px 12px 10px; color:var(--muted); font-size:11.5px; }
.win-foot a { color:var(--emerald); }
.win-foot a:hover { text-decoration:underline; }
.page-foot { margin-top:36px; padding-top:18px; border-top:1px solid var(--border); color:var(--muted); font-size:11.5px; display:flex; flex-wrap:wrap; gap:10px; justify-content:space-between; }

@media (max-width: 980px) {
  body { grid-template-columns:1fr; }
  aside { position:static; height:auto; border-right:0; border-bottom:1px solid var(--border); }
  .cat-nav { flex-direction:row; overflow-x:auto; padding-bottom:4px; }
  .cat-btn { flex:0 0 auto; border-left:0; border-bottom:2px solid transparent; border-radius:6px 6px 0 0; }
  .cat-btn.active { border-left:0; border-bottom-color:var(--emerald); }
  main { padding-top:18px; }
}
@media (max-width: 620px) {
  .grid { grid-template-columns:1fr; }
  .preview iframe { height:320px; }
  .cat-sub { display:none; }
}
</style>
</head>
<body>
<aside>
  <a class="brand" href="../">
    <span class="brand-mark">K</span>
    <span>KERNEL ATLAS<small>BLUEPRINT CONSOLE</small></span>
  </a>
  <div class="aside-label">Search</div>
  <input id="search" type="text" placeholder="标题 / 分类 / 类型...">
  <div class="aside-label">Type</div>
  <div class="chips" id="type-chips">__CHIPS__</div>
  <div class="aside-label">Categories</div>
  <nav class="cat-nav" id="cat-nav">__CATNAV__</nav>
  <button class="deep-toggle" id="deep-toggle"><span>只看深度调用链</span><b>__DEEP__</b></button>
  <div class="rail-links">
    <a href="../diagrams/">← 图集总览</a>
    <a href="../posts/?cat=linux">Linux 文章</a>
    <a href="https://github.com/zhang-ruyi/linux-arch-dia" target="_blank" rel="noopener">GitHub 仓库 ↗</a>
  </div>
</aside>
<main>
  <section class="hero">
    <p class="eyebrow">LINUX <b>v7.4.0-rc1</b> · SOURCE-BACKED</p>
    <h1>Linux 内核<em>原理图解</em></h1>
    <p class="lede">从进程、内存、网络、文件系统到块层与 NVMe;__COUNT__ 张可交互原理图,关键符号都对应真实源码的 <code>path:line</code>。</p>
    <div class="hero-stats">
      <span><strong>__COUNT__</strong>交互图</span>
      <span><strong>__CATS__</strong>分类</span>
      <span><strong>__DEEP__</strong>深度链</span>
      <span>基线 <strong>d487237</strong></span>
    </div>
    <div class="hero-actions">
      <a class="btn primary" href="./内核总览/kernel-subsystems.html" target="_blank" rel="noopener">打开总览图</a>
      <a class="btn" href="../diagrams/">图集总览</a>
      <a class="btn" href="../posts/?cat=linux">精读文章</a>
    </div>
  </section>
  <div class="statusbar">
    <span id="stats"></span>
    <button id="clear">清除筛选</button>
  </div>
__SECTIONS__
  <footer class="page-foot">
    <span>KERNEL ATLAS · Linux v7.4.0-rc1 · Archify</span>
    <span>源码基线 d487237 · __COUNT__ 张交互图 · __DEEP__ 张深度链</span>
  </footer>
</main>
<script>
(function () {
  var curType = 'all';
  var curCat = 'all';
  var deepOnly = false;

  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var sections = Array.prototype.slice.call(document.querySelectorAll('.cat-sec'));
  var typeChips = Array.prototype.slice.call(document.querySelectorAll('#type-chips .chip'));
  var catBtns = Array.prototype.slice.call(document.querySelectorAll('.cat-btn'));
  var stats = document.getElementById('stats');
  var search = document.getElementById('search');
  var deepToggle = document.getElementById('deep-toggle');

  function applyFilters() {
    var q = (search.value || '').trim().toLowerCase();
    var visible = 0;
    cards.forEach(function (card) {
      var okType = curType === 'all' || card.dataset.type === curType;
      var okCat = curCat === 'all' || card.dataset.category === curCat;
      var okDeep = !deepOnly || card.dataset.deep === '1';
      var okSearch = !q || (card.dataset.search || '').indexOf(q) !== -1;
      var show = okType && okCat && okDeep && okSearch;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    sections.forEach(function (sec) {
      var any = Array.prototype.some.call(sec.querySelectorAll('.card'), function (c) {
        return c.style.display !== 'none';
      });
      sec.style.display = any ? '' : 'none';
    });
    stats.textContent = '显示 ' + visible + ' / ' + cards.length + ' 张';
  }

  typeChips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      curType = chip.dataset.type;
      typeChips.forEach(function (c) { c.classList.toggle('active', c === chip); });
      applyFilters();
    });
  });

  catBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var cat = btn.dataset.cat;
      if (cat === 'all') {
        curCat = 'all';
        catBtns.forEach(function (b) { b.classList.toggle('active', b.dataset.cat === 'all'); });
      } else if (curCat === cat) {
        curCat = 'all';
        catBtns.forEach(function (b) { b.classList.toggle('active', b.dataset.cat === 'all'); });
      } else {
        curCat = cat;
        catBtns.forEach(function (b) { b.classList.toggle('active', b === btn); });
      }
      applyFilters();
      if (btn.dataset.target) {
        var target = document.getElementById(btn.dataset.target);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  deepToggle.addEventListener('click', function () {
    deepOnly = !deepOnly;
    deepToggle.classList.toggle('active', deepOnly);
    applyFilters();
  });

  search.addEventListener('input', applyFilters);

  document.getElementById('clear').addEventListener('click', function () {
    curType = 'all'; curCat = 'all'; deepOnly = false;
    search.value = '';
    typeChips.forEach(function (c) { c.classList.toggle('active', c.dataset.type === 'all'); });
    catBtns.forEach(function (b) { b.classList.toggle('active', b.dataset.cat === 'all'); });
    deepToggle.classList.remove('active');
    applyFilters();
  });

  applyFilters();
})();
</script>
</body>
</html>
"""
    page = (page
            .replace("__TITLE__", html.escape(title))
            .replace("__CHIPS__", "".join(chips))
            .replace("__CATNAV__", "".join(cat_nav))
            .replace("__SECTIONS__", "".join(section_html))
            .replace("__COUNT__", str(len(items)))
            .replace("__CATS__", str(len(ordered)))
            .replace("__DEEP__", str(deep_count)))
    return page


def main():
    ap = argparse.ArgumentParser(description="构建 Archify 图表画廊首页")
    ap.add_argument("candidates_dir", nargs="?", default=".archify")
    ap.add_argument("site_dir", nargs="?", default="site")
    ap.add_argument("--title", default="Linux 内核原理图解")
    args = ap.parse_args()

    items = collect(args.candidates_dir, args.site_dir)
    if not items:
        sys.exit("错误:没有找到已 finalize 的 Archify 图表候选")

    page = build_page(items, args.title)
    out = Path(args.site_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")

    cats = len(set(i["category"] for i in items))
    print(f"✓ 已生成 {out}/index.html(共 {len(items)} 张 Archify 图,{cats} 个分类)")
    print(f"  查看:python3 -m http.server 8000 -d {out} 后访问 http://localhost:8000")


if __name__ == "__main__":
    main()
