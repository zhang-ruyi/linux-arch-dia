# Linux 内核原理图解(Archify)

用 [Archify](https://github.com/tt-a1i/archify) 对 Linux 内核源码进行分析,生成可交互的架构图、流程图、时序图和状态机,并在一个静态画廊首页中集中展示。

- 所有图都是独立、可离线打开的 HTML(自带明暗主题、动效、缩放与导出)
- 每张图的主元素都标注了已核实的源码 `path:line`
- 图源是可编辑的 JSON-IR(`.archify/*/candidate.json`),不是渲染后的死图
- 当前图集:**58 张**(51 张概览/专题 + 7 张函数级深度调用链),源码基线 Linux `d487237`(v7.4.0-rc1)

## 图集一览

| 分类 | 数量 | 内容 |
|---|---|---|
| 内核总览 | 1 | 子系统分解总览 |
| 进程管理 | 9 | fork、进程状态、EEVDF 调度、上下文切换、信号、退出回收、中断下半部、futex + fork 深度链 |
| 内存管理 | 8 | 缺页异常、伙伴系统、SLUB、mmap、page cache 读、页回收 + 缺页深度链 + memblock→folio |
| 网络协议栈 | 8 | TCP 握手/挥手/状态机、NAPI 收包、发包路径、socket 创建、epoll + TCP 收包深度链 |
| 文件系统 | 8 | VFS 架构、open、dentry 查找、读写路径、脏页写回、ext4 磁盘布局 + open/read 深度链 |
| 设备驱动 | 4 | 总线-设备-驱动模型、块 IO、内核启动 + 块层深度链 |
| NVMe 驱动 | 8 | 初始化、识别与命名空间扫描、支持范围与限制、用户态 I/O 路径、SQ/CQ 门铃、io_uring 透传、控制器状态机 + NVMe IO 深度链 |
| 内核驱动框架 | 4 | device/driver/bus 模型、probe 绑定时序、devres 生命周期、file_operations 分发 |
| 存储技术 | 1 | io_uring / libaio / POSIX AIO 三种异步 IO |
| 并发与同步 | 1 | 并发原语选择决策流程(RCU / seqlock / per-CPU / 锁) |
| LLM 推理 | 6 | vLLM 架构/请求生命周期/PagedAttention、LMCache 架构/KV 流、联合请求链路 |

深度调用链(函数级,`deep-*`):fork 创建进程、缺页异常、TCP 收包、open 路径解析、read 到块层、块层 IO、NVMe IO。每张概览图内还附有一张「完整调用链(源码核实)」卡片,按真实调用顺序列出函数与 `path:line`。

## 目录结构

```
.
├── site/                         # 部署目录:index.html + <分类>/<图>.html
├── .archify/                     # 图源:candidate.json 与 finalize 回执
│   └── <type>-<slug>/candidate.json
├── diagrams/                     # 旧 Mermaid 源(仅作迁移参考,新流程不再使用)
├── .opencode/
│   ├── agents/kernel-diagrammer.md
│   └── skills/kernel-diagrams/
│       ├── SKILL.md              # 分析→作图→校验 方法论
│       └── scripts/build_site.py # 画廊首页生成器
└── README.md
```

## 部署

站点是纯静态文件,不需要后端。

### 方式一:本地 / 内网(推荐)

```bash
git clone git@github.com:zhang-ruyi/linux-arch-dia.git
cd linux-arch-dia

# 默认 8000 端口,绑定所有网卡,局域网可访问
python3 -m http.server 8000 -d site --bind 0.0.0.0
```

- 本机访问 http://127.0.0.1:8000
- 局域网访问 http://<本机IP>:8000

注意:

- 请通过 HTTP 访问,不要用 `file://` 直接打开 `site/index.html`(首页用 iframe 预览,部分浏览器会限制本地 iframe)
- 若浏览器配置了代理,访问内网 IP 可能得到 502,请把 `127.0.0.1` 和本机 IP 加入代理例外(或临时关闭代理)

### 方式二:nginx

```nginx
server {
    listen 8000;
    server_name _;
    root /path/to/linux-arch-dia/site;
    index index.html;
    location / {
        try_files $uri $uri/ =404;
    }
}
```

### 方式三:systemd 常驻(可选)

`~/.config/systemd/user/linux-arch-dia.service`:

```ini
[Unit]
Description=Linux kernel Archify gallery
After=network.target

[Service]
WorkingDirectory=/path/to/linux-arch-dia
ExecStart=/usr/bin/python3 -m http.server 8000 -d site --bind 0.0.0.0
Restart=on-failure

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now linux-arch-dia
```

### 方式四:GitHub Pages(可选)

仓库的站点位于 `site/` 子目录。用 GitHub Actions 将 `site/` 发布到 Pages(或用任意 CI 把 `site/` 同步到静态托管),不要直接选仓库根目录作为 Pages 源。

## 更新已有图

1. 编辑图源,例如 `.archify/sequence-fork-process-creation/candidate.json`
2. 重新校验并生成 HTML:

   ```bash
   export ARCHIFY_CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
   export ARCHIFY_CHROME_NO_SANDBOX=1

   node ~/.agents/skills/archify/bin/archify.mjs finalize sequence \
     .archify/sequence-fork-process-creation/candidate.json \
     site/进程管理/fork-process-creation.html \
     --repo-root ~/workspace/Git/git.kernel.org/linux \
     --quality showcase --json
   ```

   如果该图之前已经生成过(已有 browser-check 证据),重跑时加独立输出目录,避免覆盖旧证据:

   ```bash
   ... --out-dir .archify/sequence-fork-process-creation/review-$(date +%s)
   ```

3. 重建首页:

   ```bash
   python3 .opencode/skills/kernel-diagrams/scripts/build_site.py .archify site --title "Linux 内核原理图解"
   ```

4. 提交并推送:

   ```bash
   git add -A && git commit -m "Update <图名>" && git push
   ```

## 追加新图

### 0. 前置:安装 Archify(新机器首次)

Archify 运行时要求 Node.js >= 18;`skills` 安装器要求 Node.js >= 22.20。

```bash
# 安装 skill 到 opencode 全局目录(会复制到 ~/.agents/skills/archify)
npx -y skills@latest add https://github.com/tt-a1i/archify \
  --skill archify --agent opencode --global --copy --yes

# 自检,应输出 Archify is ready.
node ~/.agents/skills/archify/bin/archify.mjs doctor
```

`browser-check` 门禁需要 Chrome/Chromium。无桌面环境时可用 headless shell:

```bash
mkdir -p ~/.cache/archify-chrome
curl -sL -o /tmp/chrome-headless.zip \
  https://storage.googleapis.com/chrome-for-testing-public/132.0.6834.159/linux64/chrome-headless-shell-linux64.zip
unzip -q /tmp/chrome-headless.zip -d ~/.cache/archify-chrome

export ARCHIFY_CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
export ARCHIFY_CHROME_NO_SANDBOX=1   # Ubuntu 下 userns 被禁用时必须
```

### 1. 分析源码并核实符号

源码树示例:`~/workspace/Git/git.kernel.org/linux`。

```bash
# 找定义
grep -rn "handle_mm_fault" mm/memory.c | head
# 找调用者
grep -rn "handle_mm_fault(" --include="*.c" | grep -v "handle_mm_fault(struct"
# 取当前 HEAD,写入 candidate 的 meta.repository.revision
git -C ~/workspace/Git/git.kernel.org/linux rev-parse HEAD
```

规则:写进图的每个函数名、结构体名、行号都必须在源码树中 `grep` 核实,不要凭记忆(例如 `do_filp_open` 自 7.2 起改名为 `do_file_open`,`send_signal` 为 `send_signal_locked`)。

### 2. 选择图表类型

| 需求 | `diagram_type` |
|---|---|
| 组件、模块、边界、层次结构 | `architecture` |
| 单条控制流的分支与步骤 | `workflow` |
| 多实体按时间交互(系统调用、协议握手) | `sequence` |
| 状态迁移(进程、TCP、页) | `lifecycle` |
| 树形包含、子系统分解 | `tree` |
| 结构体 / ops 关系 | `class` |
| 管道、数据流 | `dataflow` |
| 带时间戳的事件、耗时分解 | `timeline` / `waterfall` |

旧 Mermaid 迁移映射:`flowchart`→`workflow`、`graph`→`architecture`、`sequenceDiagram`→`sequence`、`stateDiagram`→`lifecycle`。只取语义与拓扑,不要照搬样式。

### 3. 编写 candidate.json

路径约定:`.archify/<type>-<slug>/candidate.json`;产物约定:`site/<中文分类>/<slug>.html`。

最小可用的 `sequence` 示例(已通过全部门禁):

```json
{
  "schema_version": 1,
  "diagram_type": "sequence",
  "meta": {
    "title": "示例:read() 读文件时序图",
    "locale": "zh-CN",
    "output": "site/文件系统/example-read.html",
    "quality_profile": "showcase",
    "repository": {
      "url": "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git",
      "revision": "<git rev-parse HEAD 的 40 位>",
      "link_mode": "local-only"
    }
  },
  "participants": [
    { "id": "app", "type": "external", "label": "用户进程", "sources": [{ "path": "fs/read_write.c", "line": 705 }] },
    { "id": "vfs", "type": "backend", "label": "VFS 层", "sources": [{ "path": "fs/read_write.c", "line": 554 }] },
    { "id": "fs", "type": "backend", "label": "ext4", "sources": [{ "path": "fs/ext4/file.c", "line": 130 }] }
  ],
  "messages": [
    { "from": "app", "to": "vfs", "y": 180, "label": "read()" },
    { "from": "vfs", "to": "fs", "y": 220, "label": "read_iter()" },
    { "from": "fs", "to": "vfs", "y": 260, "label": "数据页", "variant": "return" },
    { "from": "vfs", "to": "app", "y": 300, "label": "返回字节数", "variant": "return" }
  ]
}
```

写作要点:

- 主元素(workflow 节点 / sequence 参与者 / lifecycle 状态 / architecture 组件 / tree 节点)必须带 `sources`,每条 `{path, line}`,最多 3 条;关系、箭头、迁移不带 `sources`
- `participants[].type` 取值:`frontend` / `backend` / `database` / `cloud` / `security` / `messagebus` / `external`
- `messages[].variant` 取值:`default` / `emphasis` / `security` / `dashed` / `return`
- 首条消息 `y` 不小于 160,消息间距按是否带 note 预留(无 note 约 28px 起)
- 新图不要写 `meta.viewBox`,让渲染器自动测量;只有 `browser-check` 报告视口问题才按诊断调整
- 更完整的字段以 Archify 的 `schemas/<type>.schema.json` 和 `examples/` 为准

### 4. 校验并生成

```bash
export ARCHIFY_CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
export ARCHIFY_CHROME_NO_SANDBOX=1

node ~/.agents/skills/archify/bin/archify.mjs finalize sequence \
  .archify/sequence-example-read/candidate.json \
  site/文件系统/example-read.html \
  --repo-root ~/workspace/Git/git.kernel.org/linux \
  --quality showcase --json
```

只有 `validate / deliver / check / browser-check` 四门禁全部 `pass` 才算成功。非零退出时:

1. 读输出中的 `diagnostics`(或 `*.finalize-summary.json`),按提示修复 JSON
2. 重跑完整 `finalize`;若上一轮已进入 `browser-check`,本轮加 `--out-dir .archify/<type>-<slug>/review-<n>`
3. 修复只调整表达/坐标/标签,不要删掉原本要表达的含义

### 5. 重建首页并提交

```bash
python3 .opencode/skills/kernel-diagrams/scripts/build_site.py .archify site --title "Linux 内核原理图解"
git add -A && git commit -m "Add diagram: <图名>" && git push
```

### 6. 用 agent 自动化(可选)

仓库内含 `kernel-diagrammer` agent 和 `kernel-diagrams` skill。用 opencode 打开本仓库并**重启 opencode**(配置在启动时加载)后,可以直接说:

> 用 kernel-diagrammer 分析 TCP 收包路径,画成时序图并更新站点

agent 会按 skill 的方法论定位源码、核实符号、写 candidate、跑 finalize 并重建首页。

## 常用命令速查

```bash
# 自检
node ~/.agents/skills/archify/bin/archify.mjs doctor

# 重建画廊首页
python3 .opencode/skills/kernel-diagrams/scripts/build_site.py .archify site --title "Linux 内核原理图解"

# 本地预览
python3 -m http.server 8000 -d site --bind 0.0.0.0

# 预览某一类图
ls site/*/
```

## 常见问题

| 现象 | 处理 |
|---|---|
| `viewer/chrome-unavailable` | 设置 `ARCHIFY_CHROME` 指向 Chrome/Chromium 可执行文件 |
| `No usable sandbox` | 设置 `ARCHIFY_CHROME_NO_SANDBOX=1` |
| finalize 非零退出 | 读 `diagnostics` 修复 candidate 后重跑,不要跳过 |
| 已到 browser-check 后重跑报证据冲突 | 加 `--out-dir .archify/<type>-<slug>/review-<n>` |
| 浏览器访问内网地址 502 | 绕过代理或把 `127.0.0.1` / 本机 IP 加入代理例外 |
| 新图不出现在首页 | 确认 `meta.output` 指向 `site/<分类>/<slug>.html`,且已成功 finalize,然后重建首页 |
| 打开首页样式异常 | 用 HTTP 服务访问,不要用 `file://` |

## 版权与使用限制

Copyright © 2026 zhang-ruyi (Ruyi.zhang). All rights reserved.

- **未经作者书面许可,请勿将本仓库内容(图表、图源 JSON、脚本、文档)用于任何商业用途。**
- **未经作者书面许可,请勿直接转载、复制或再发布本仓库内容。**
- 个人学习、研究、教学等非商业性使用,须保留本版权声明并注明来源(仓库地址与提交版本)。
- 商业授权、转载授权请联系:www.zhangyi.studio@gmail.com
- Linux 内核源码本身遵循其各自许可(主要为 GPL-2.0);本仓库仅包含对内核机制的分析整理与图示,不包含内核源码副本。

## 说明

- 源码基线:Linux `d48723711bae9b8cdc56719c448ba42fef28cbee`(v7.4.0-rc1);图的 `meta.repository` 使用 `link_mode: "local-only"`,便于在任意机器上复现
- “四门禁通过”是自动化校验(结构、交付、可复现性、真实浏览器视图),不等同于人工视觉审查;需要视觉复核时可对单图运行 Archify 的 `visual-check`
- `diagrams/` 中的 `.mmd` 是早期 Mermaid 版本,保留仅作溯源;仓库的正式产物是 `site/` 与 `.archify/`
- Archify 为第三方开源工具(Apache-2.0),该许可仅适用于 Archify 本身;本仓库原创图表与文档的版权与使用限制以上一节为准
