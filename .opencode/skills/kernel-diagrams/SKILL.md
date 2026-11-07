---
name: kernel-diagrams
description: 用 Archify 分析大型 C 源码项目(默认 Linux 内核 ~/workspace/Git/git.kernel.org/linux),生成可交互的架构图/流程图/时序图/状态机等独立 HTML,并构建画廊首页展示。Use when 用户要求"分析内核、画原理图/时序图/流程图、展示到网页"。
---

# Kernel Diagrams(Archify 方案)

本 skill 提供"阅读大型 C 源码 → 用 Archify 生成可交互原理图 → 画廊首页集中展示"的完整工具链。配合 `kernel-diagrammer` agent 使用(推荐),也可在任意 agent 中遵循本规范。

Archify 已全局安装在 `~/.agents/skills/archify`,命令行入口:
`node ~/.agents/skills/archify/bin/archify.mjs`

## 一、前置条件

1. 自检(应输出 Archify is ready):
   ```bash
   node ~/.agents/skills/archify/bin/archify.mjs doctor
   ```
2. 浏览器门禁 `browser-check` 需要 Chrome/Chromium。本机已备好 headless shell:
   ```bash
   export ARCHIFY_CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
   export ARCHIFY_CHROME_NO_SANDBOX=1
   ```
   `ARCHIFY_CHROME_NO_SANDBOX=1` 是 Ubuntu 下 unprivileged userns 被禁时的必要开关。
   若该路径不存在,下载 `chrome-headless-shell` 到同一目录,或自行安装 Chrome 并设置 `ARCHIFY_CHROME`。

## 二、目录与产物约定

```
项目根/
  .archify/<type>-<slug>/candidate.json   # 图表 JSON-IR 源(手工/agent 编写)
  site/<中文分类>/<slug>.html             # finalize 生成的独立交互图
  site/index.html                         # 画廊首页(脚本生成)
  diagrams/                               # 【遗留】旧 Mermaid 源,仅作迁移参考,新流程不使用
```

- 分类用中文目录名:进程管理、内存管理、网络协议栈、文件系统、设备驱动、内核总览
- 文件名:`<type>-<slug>` 全小写英文短横线
- 内核仓库身份(固定):
  `url=https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`
  运行 `git -C ~/workspace/Git/git.kernel.org/linux rev-parse HEAD` 取当前 40 位 revision;`link_mode="local-only"`

## 三、工作流

### 1. 明确目标并定位源码

- 系统调用:`grep -rn "SYSCALL_DEFINE" kernel/ fs/ mm/ net/ | grep 关键字`
- 协议:收包 `*_rcv`,发包 `*_xmit` / `*_connect`
- 驱动:`probe` 函数、`module_init`
- 机制:先读 `Documentation/` 对应文档,再对照源码

### 2. 追踪调用链

1. `grep -n "函数名" 路径` 找定义,`read` 读主线,跳过错误分支细节
2. 遇到 ops 结构(`file_operations`/`net_device_ops`):先找注册点,再追具体实现
3. 关键宏展开一层(`SYSCALL_DEFINEx`)
4. **每个要写进图的函数/结构体名和行号都必须 grep 核实**,不得凭记忆(7.4 等新版本中符号与行号仍在变化,如 `do_file_open`、`send_signal_locked`、`get_signal`)

### 3. 选 Archify 类型

| 需求 | Archify type |
|---|---|
| 模块/组件/边界/层次结构 | `architecture` |
| 单条控制流的分支与步骤 | `workflow` |
| 多实体按时间交互(系统调用、握手) | `sequence` |
| 状态迁移(进程/TCP/页) | `lifecycle` |
| 树形包含/子系统分解 | `tree` |
| 结构体/ops 关系 | `class` |
| 管道/数据流 | `dataflow` |
| 带时间戳的事件 | `timeline` / `waterfall` |

旧 Mermaid 迁移映射:`flowchart`→`workflow`,`graph`→`architecture`,`sequenceDiagram`→`sequence`,`stateDiagram`→`lifecycle`,`erDiagram`→`erd`,`classDiagram`→`class`。只取语义和拓扑,不照搬 Mermaid 样式。

### 4. 写候选 JSON(权威规范在 Archify skill 内)

**先读**(不可跳过):
- `~/.agents/skills/archify/SKILL.md`
- `~/.agents/skills/archify/references/authoring-defaults.md`
- `~/.agents/skills/archify/references/repository-authoring.md`
- `~/.agents/skills/archify/schemas/common.schema.json` 及所选 type 的 `schemas/<type>.schema.json`
- 对应 `examples/*` 示例

然后写 `.archify/<type>-<slug>/candidate.json`,必须包含:

```json
{
  "schema_version": 1,
  "diagram_type": "<type>",
  "meta": {
    "title": "中文标题",
    "locale": "zh-CN",
    "output": "site/<分类>/<slug>.html",
    "quality_profile": "showcase",
    "repository": {
      "url": "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git",
      "revision": "<40位 HEAD>",
      "link_mode": "local-only"
    }
  },
  "...": "所选 type 的拓扑字段"
}
```

要点:
- 主元素(workflow 节点 / sequence 参与者 / lifecycle 状态 / architecture 组件 / tree 节点)必须带 `sources`,每条 `{path, line}`,最多 3 条;关系/箭头/迁移不带 sources
- 标签用中文,符号名保留源码真实拼写
- 关系标签承载语义,不要为空;`meta.legend` 仅在需要说明变体时使用
- 新图省略 `meta.viewBox`,让渲染器自动测量;仅在浏览器门禁报告视口问题时按诊断设置

### 5. finalize(校验 + 交付 + 浏览器检查)

```bash
export ARCHIFY_CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
export ARCHIFY_CHROME_NO_SANDBOX=1
node ~/.agents/skills/archify/bin/archify.mjs finalize <type> \
  .archify/<type>-<slug>/candidate.json \
  site/<分类>/<slug>.html \
  --repo-root /home/zhang/workspace/Git/git.kernel.org/linux \
  --quality showcase --json
```

- 四门禁 `validate → deliver → check → browser-check` 全 pass 才算成功
- 非零退出不是成功:读 `diagnostics` 修复 candidate 后重跑
- 一旦某轮到达 `browser-check`,后续重跑必须加 `--out-dir .archify/<type>-<slug>/review-<n>`
- 修复只调整语义表达/坐标/标签,不得删除用户要求的含义

### 6. 构建画廊并查看

```bash
python3 .opencode/skills/kernel-diagrams/scripts/build_site.py .archify site --title "Linux 内核原理图解"
python3 -m http.server 8000 -d site --bind 0.0.0.0
```

首页扫描 `.archify/*/candidate.json`,自动生成分类侧栏、搜索、类型筛选和 iframe 预览。

### 调用链深度约定(两层)

为避免版面拥挤,采用两层表达:

1. **概览图**(现有 37 张):节点按阶段聚合,但每张图的 `cards` 中必须有一张:
   `{"dot":"slate","title":"完整调用链(源码核实)","items":["函数 — path:line", ...]}`
   按真实调用顺序逐函数列出完整链,函数名与行号必须 grep 核实。
2. **函数级深度调用图**(`deep-*`):用 `workflow` 类型,节点就是函数,`sublabel` 写文件/职责,用 group 分阶段,允许 25–50 个节点;主元素带 `sources`。
   当前覆盖:进程创建、缺页异常、TCP 收包、open、read、块层 IO、NVMe IO。

修改已有概览图后必须重跑 `finalize` 并加新的 `--out-dir .../review-<N>`(原产物已持有 browser-check 证据)。

## 四、内核分析速查

| 主题 | 入口线索 |
|---|---|
| 进程创建 | `kernel_clone()` kernel/fork.c → `copy_process()` |
| 进程调度 | `schedule()` → `__schedule()` → `pick_task_fair()`/`pick_eevdf()` |
| 缺页异常 | `exc_page_fault()` → `handle_mm_fault()` → `handle_pte_fault()` |
| 内存分配 | `alloc_pages()` → `__alloc_pages_noprof()` → `rmqueue()`;`kmalloc` → `__kmalloc_noprof()` |
| 文件打开 | `do_sys_open()` → `do_file_open()` → `path_openat()` |
| 文件读写 | `vfs_read()` → `f_op->read_iter` → `filemap_read()` |
| 写回 | `balance_dirty_pages()` → `wb_workfn()` → `writeback_sb_inodes()` |
| TCP 收包 | `tcp_v4_rcv()` → `tcp_v4_do_rcv()` → `tcp_rcv_state_process()` |
| TCP 发包 | `tcp_sendmsg()` → `tcp_write_xmit()` → `ip_queue_xmit()` → `dev_queue_xmit()` |
| NAPI 收包 | 硬中断 → `napi_schedule` → `net_rx_action` → `napi_poll` → `netif_receive_skb` |
| epoll | `eventpoll`(rbtree + rdllist)、`ep_poll_callback`、`ep_poll` |
| 驱动模型 | `driver_register()` → `bus_add_driver()` → `driver_attach()` → `really_probe()` |
| 块 IO | `submit_bio()` → `submit_bio_noacct()` → `blk_mq_submit_bio()` → `bio_endio()` |
| NVMe 初始化 | `nvme_probe()` → `nvme_pci_enable()` → `nvme_init_ctrl_finish()` → `nvme_start_ctrl()` |
| NVMe I/O | `nvme_queue_rq()` → SQ tail 门铃 → `nvme_irq()` → `nvme_handle_cqe()` → `nvme_complete_rq()` |
| NVMe 复位 | `nvme_timeout()` → `nvme_reset_ctrl()` → `nvme_reset_work()` |
| 中断下半部 | `raise_softirq`/`do_softirq`、`tasklet`、`queue_work`/`worker_thread` |
| 启动 | `startup_64` → `start_kernel()` → `rest_init()` → `kernel_init()` |

## 五、质量自检

- [ ] 图中每个函数/结构体名与行号都能在源码树 grep 到
- [ ] 主元素都有 `sources`,路径为仓库相对路径
- [ ] `finalize` 四门禁全部 pass
- [ ] `build_site.py` 生成 `site/index.html`,`http.server` 能访问
- [ ] 报告标注所用内核版本/HEAD;未做人工视觉审查时明确说明"自动检查通过,未做视觉复核"

## 六、遗留说明

`diagrams/` 下的 `.mmd` 是旧 Mermaid 方案的迁移来源,保留仅供溯源。新的图一律走 Archify;如需从旧图迁移,读取其语义后重新创作 Archify JSON,不要机械转样式。
