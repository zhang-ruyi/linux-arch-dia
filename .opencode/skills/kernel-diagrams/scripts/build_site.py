#!/usr/bin/env python3
"""构建 Archify 图表画廊首页。

扫描候选目录下的 */candidate.json,读取 diagram_type / meta.title / meta.output,
生成站点首页 index.html:分类侧栏 + 搜索 + 类型筛选 + iframe 预览 + 打开链接。

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
TYPE_ORDER = list(TYPE_LABELS.keys())


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

    type_present = OrderedDict()
    for it in items:
        type_present.setdefault(it["type"], TYPE_LABELS.get(it["type"], it["type"]))

    cards = []
    for it in items:
        label = TYPE_LABELS.get(it["type"], it["type"])
        sub = f'<p class="desc">{html.escape(it["subtitle"])}</p>' if it["subtitle"] else ""
        searchable = f'{it["title"]} {it["subtitle"]} {it["category"]} {it["type"]}'.lower()
        cards.append(f'''
      <article class="card" data-type="{html.escape(it['type'])}"
               data-category="{html.escape(it['category'])}"
               data-search="{html.escape(searchable)}">
        <header class="card-head">
          <h3>{html.escape(it["title"])}</h3>
          <span class="badge badge-{html.escape(it['type'])}">{html.escape(label)}</span>
        </header>
        {sub}
        <div class="preview">
          <iframe src="{html.escape(it['rel'])}" loading="lazy" title="{html.escape(it['title'])}"></iframe>
        </div>
        <footer class="card-foot">
          <span class="cat">{html.escape(it["category"])}</span>
          <a class="open" href="{html.escape(it['rel'])}" target="_blank" rel="noopener">打开交互图 ↗</a>
        </footer>
      </article>''')

    toc = []
    for cat, arr in cats.items():
        links = "".join(
            f'<li><a href="#{html.escape(it["slug"])}">{html.escape(it["title"])}</a></li>'
            for it in arr
        )
        toc.append(f'''
      <div class="toc-cat">
        <button class="toc-cat-head" onclick="setCategory('{html.escape(cat)}')">
          {html.escape(cat)} <span class="count">{len(arr)}</span>
        </button>
        <ul class="toc-items">{links}</ul>
      </div>''')

    chips = '<button class="chip active" data-type="all" onclick="setType(\'all\')">全部</button>'
    for t, label in type_present.items():
        chips += (
            f'<button class="chip" data-type="{html.escape(t)}" '
            f'onclick="setType(\'{html.escape(t)}\')">{html.escape(label)}</button>'
        )

    page = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>""" + html.escape(title) + """</title>
<style>
:root {
  --bg:#0e1319; --panel:#151d26; --card:#1a2430; --border:#29343f;
  --text:#dce5ef; --muted:#8b9aab; --accent:#57a8ff; --hover:#22303f;
}
html[data-theme="light"] {
  --bg:#f2f5f9; --panel:#fff; --card:#fff; --border:#dbe2ea;
  --text:#182230; --muted:#5b6b7c; --accent:#1668c4; --hover:#edf3fa;
}
* { box-sizing:border-box; margin:0; padding:0; }
body { display:flex; min-height:100vh; background:var(--bg); color:var(--text);
  font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif; }
aside { width:280px; flex-shrink:0; height:100vh; position:sticky; top:0; overflow-y:auto;
  background:var(--panel); border-right:1px solid var(--border); padding:20px 16px; }
aside h1 { font-size:18px; }
aside .sub { color:var(--muted); font-size:12px; margin:4px 0 16px; }
#search { width:100%; padding:8px 12px; border-radius:8px; border:1px solid var(--border);
  background:var(--bg); color:var(--text); font-size:13px; outline:none; }
#search:focus { border-color:var(--accent); }
.toc-cat { margin-top:14px; }
.toc-cat-head { width:100%; text-align:left; background:none; border:none; color:var(--text);
  font-size:14px; font-weight:600; cursor:pointer; padding:6px 4px; border-radius:6px;
  display:flex; justify-content:space-between; align-items:center; }
.toc-cat-head:hover { background:var(--hover); color:var(--accent); }
.count { background:var(--hover); color:var(--muted); font-size:11px; border-radius:10px; padding:1px 8px; font-weight:400; }
.toc-items { list-style:none; padding-left:10px; }
.toc-items a { display:block; color:var(--muted); text-decoration:none; font-size:12.5px;
  padding:3px 6px; border-radius:5px; }
.toc-items a:hover { color:var(--accent); background:var(--hover); }
main { flex:1; padding:24px 28px; }
.toolbar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:12px;
  position:sticky; top:0; z-index:5; background:var(--bg); padding:10px 0; }
.chip { border:1px solid var(--border); background:var(--panel); color:var(--muted);
  padding:5px 14px; border-radius:999px; font-size:12.5px; cursor:pointer; }
.chip.active { background:var(--accent); border-color:var(--accent); color:#fff; }
.chip:hover { border-color:var(--accent); color:var(--accent); }
#theme-toggle, #clear-filter { border:none; background:none; color:var(--accent);
  cursor:pointer; font-size:12.5px; }
#theme-toggle { border:1px solid var(--border); background:var(--panel); color:var(--muted);
  padding:5px 12px; border-radius:999px; }
#clear-filter { margin-left:auto; }
#stats { color:var(--muted); font-size:12.5px; margin-bottom:14px; }
#cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(520px,1fr)); gap:18px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; }
.card-head { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.card h3 { font-size:15.5px; }
.desc { color:var(--muted); font-size:12.5px; line-height:1.5; margin-top:6px; }
.badge { font-size:11px; padding:2px 9px; border-radius:999px; white-space:nowrap; flex-shrink:0; }
.badge-architecture { background:#173a5e; color:#7cc0ff; }
.badge-workflow { background:#174a2e; color:#7ee0a8; }
.badge-sequence { background:#3d1a5e; color:#d3a0ff; }
.badge-lifecycle { background:#4a3a17; color:#ffd77c; }
.badge-tree { background:#4a1a2e; color:#ff9cc0; }
.badge-dataflow, .badge-erd, .badge-class, .badge-timeline, .badge-waterfall { background:#26313d; color:#a9bfd4; }
.preview { margin-top:10px; border:1px solid var(--border); border-radius:8px; overflow:hidden; background:var(--panel); }
.preview iframe { width:100%; height:420px; border:0; display:block; }
.card-foot { display:flex; justify-content:space-between; align-items:center; margin-top:10px;
  color:var(--muted); font-size:12px; }
.card-foot .open { color:var(--accent); text-decoration:none; }
.card-foot .open:hover { text-decoration:underline; }
</style>
</head>
<body>
<aside>
  <h1>""" + html.escape(title) + """</h1>
  <div class="sub">Archify 交互式内核原理图 · 共 """ + str(len(items)) + """ 张</div>
  <input id="search" type="text" placeholder="搜索标题 / 分类 / 类型..." oninput="applyFilters()">
""" + "\n".join(toc) + """
</aside>
<main>
  <div class="toolbar">
""" + chips + """
    <button id="clear-filter" onclick="clearFilters()">清除筛选</button>
    <button id="theme-toggle" onclick="toggleTheme()">浅色模式</button>
  </div>
  <div id="stats"></div>
  <div id="cards">
""" + "\n".join(cards) + """
  </div>
</main>
<script>
let curCategory = 'all';
let curType = 'all';

function applyFilters() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  let visible = 0;
  document.querySelectorAll('.card').forEach(card => {
    const okCat = curCategory === 'all' || card.dataset.category === curCategory;
    const okType = curType === 'all' || card.dataset.type === curType;
    const okSearch = !q || card.dataset.search.includes(q);
    const show = okCat && okType && okSearch;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.getElementById('stats').textContent =
    '显示 ' + visible + ' / ' + document.querySelectorAll('.card').length + ' 张';
}

function setCategory(cat) {
  curCategory = (curCategory === cat) ? 'all' : cat;
  applyFilters();
}

function setType(t) {
  curType = t;
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('active', c.dataset.type === t));
  applyFilters();
}

function clearFilters() {
  curCategory = 'all'; curType = 'all';
  document.getElementById('search').value = '';
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('active', c.dataset.type === 'all'));
  applyFilters();
}

function toggleTheme() {
  const root = document.documentElement;
  const toLight = root.getAttribute('data-theme') !== 'light';
  root.setAttribute('data-theme', toLight ? 'light' : 'dark');
  document.getElementById('theme-toggle').textContent = toLight ? '深色模式' : '浅色模式';
  localStorage.setItem('kd-theme', toLight ? 'light' : 'dark');
}

(function () {
  if (localStorage.getItem('kd-theme') === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    document.getElementById('theme-toggle').textContent = '深色模式';
  }
  applyFilters();
})();
window.addEventListener('load', applyFilters);
</script>
</body>
</html>
"""
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
