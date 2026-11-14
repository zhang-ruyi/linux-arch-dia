# AGENTS.md

本文件面向后续接手本项目的 agent/开发者。先读这里,再读具体 skill。

## 1. 项目是什么

用**源码证据**把 Linux 内核与 LLM 推理系统拆成:

1. **可交互图集**:Archify 生成独立 HTML,带深/浅色、动效、导出;Linux 与 LLM 两套 UI 风格必须区分。
2. **源码级长文**:Jekyll 博客 + 微信公众号;强调“数据现在在哪、以什么形态存在”,不堆字段清单。
3. **可复用组件/skill**:布局图、层级图、内核图解、微信原生文章流程。

核心原则:

- 图里的符号、函数、行号必须来自实际源码,用 `grep -n` / `rg` 核实,禁止凭记忆。
- 文章先给结论/数据视图,再解释“为什么”;调用链可保留代码块,便于复制对照。
- 微信文章优先原生内联 HTML + CSS 图卡,不用表格、不依赖图片。

## 2. 仓库与目录

| 路径 | 远端 | 作用 |
|---|---|---|
| `/home/zhang/opencode/code_analsys` | `zhang-ruyi/linux-arch-dia` | Linux 图集源码、`.archify/` 候选、`site/` 产物;本文件所在仓库 |
| `/tmp/opencode/llm-arch-dia-repo` | `zhang-ruyi/llm-arch-dia` | LLM 图集(vLLM/LMCache),Bento UI |
| `/tmp/opencode/ruy-blog` | `zhang-ruyi/ruy` | Jekyll 博客、文章、微信 `wechat/` 源文件与产物 |
| `/tmp/opencode/skills-repo` | `zhang-ruyi/skills` | 可复用 skill 归档(含 `wechat-article`) |
| `/home/zhang/opencode/workspace/` | (本地) | **新工具/项目的默认存放目录**,每个项目一个子目录 |
| `~/opencode/workspace/ruy` | `zhang-ruyi/ruy` | 博客源码(持久位置);`/tmp` 下的旧 clone 已清理 |
| `~/opencode/workspace/ruy-fnos` | (待归档) | 博客 → 飞牛 fnOS 原生应用工程(`build.sh` / `deploy.sh`) |
| `~/opencode/workspace/clash-doctor` | `zhang-ruyi/clash-doctor` | 软路由代理体检工具 |
| `~/opencode/workspace/daily-digest` | `zhang-ruyi/daily-digest` | 每日 4 批 AI/内核/半导体新闻推送(企微),路由 cron 运行 |
| `~/opencode/workspace/llm-arch-dia` | `zhang-ruyi/llm-arch-dia` | LLM 图集源码(含构建产物 `site/`) |

注意:

- **新工具、脚本、实验项目默认放 `/home/zhang/opencode/workspace/<project>/`**;不要再放 `/tmp/opencode`(实测会被清理,2026-11-15 已发生过)。

- `/tmp/opencode` 是临时工作区,可能被清理。缺失时用 SSH 重新 clone:`git@github.com:zhang-ruyi/<repo>.git`。
- 博客线上地址:`https://zhang-ruyi.github.io/ruy/`;permalink 为 `/:year/:month/:day/:title.html`。
- 本地服务目录映射:`/tmp/opencode/serve/ruy` → `/tmp/opencode/_site_test`,端口 8123。
- **飞牛 NAS**:`192.168.5.53`(Web 5666;应用端口 8899)。SSH 用户 `zhang`,已加入本机公钥 `~/.ssh/id_ed25519_router`;`sudo` 需密码,脚本用 `FNOS_PW` 环境变量传入,不写入仓库。
- 内核源码默认:`/home/zhang/workspace/Git/linux`(2026-11-15 由 `~/workspace/Git/git.kernel.org/linux` move 而来;origin 已改为 `https://github.com/zhang-ruyi/linux.git` fork)。
- 本地 vLLM/LMCache checkout 的 origin 是 `zhang-ruyi/vllm`、`zhang-ruyi/LMCache`(不是上游);Archify `meta.repository.url` 必须与实际 origin 一致,否则 repository-evidence 门禁失败。

## 3. 当前基线

| 项目 | 基线 |
|---|---|
| Linux 内核 | `d48723711bae9b8cdc56719c448ba42fef28cbee`(v7.4.0-rc1) |
| vLLM | `c724bb35d4e70201cf0fa6f2f1dcd802c6f9dad4` |
| LMCache | `a4a688827def88f1df3e9af5fad43245913fca36` |

## 4. 已完成

### Linux 图集

- 基线迁移到 v7.4.0-rc1,全图重跑,486 条卡片引用校验。
- 58 张图 / 10 分类,含 7 张 `deep-*` 函数级链;内核总览 7 张。
- 新增/重做:syscall-overview、io-stack-overview、interrupt-overview、memory-overview、user-kernel-entry、entry-taxonomy、concurrency-primitives。
- 删除 concurrency-overview(用户认为“鸡肋”)。
- 修复 kernel-subsystems / nvme-support-scope 版本标签;修复 deep-nvme-io 空白;树图改 down 布局。
- UI:Blueprint Console(左侧轨 + 分区网格 + 终端窗卡),侧栏 14px,背景提亮。

### LLM 图集

- 7 张:vLLM×3、LMCache×2、联合×2;独立仓库 + 博客 submodule。
- UI:Bento;宽度 `min(1800px, 96vw)`。

### 博客与文章

- 首页 → `/diagrams/` → `/linux-arch-dia/` + `/llm-arch-dia/` 三级结构。
- 文章:io-data-journey(IO 数据变形记)、vllm-lmcache-long-session(超长会话 KV)、vllm-internals、lmcache-internals、vllm-lmcache-overview 等。
- 文章图示用自研 CSS 组件(dataflow/journey/io-box/layout-map/tree-map),不嵌 Archify iframe。
- 版权信息:© 2026 zhang-ruyi;禁商用/禁转载;联系 `www.zhangyi.studio@gmail.com`。

### 微信文章

- 两篇已生成公众号原生 HTML:
  - 《一次 IO 的数据变形记:从用户页到 NAND 页》
  - 《超长会话的 KV 数据流:GPU 建块、L1 成对象、L2 落 NVMe,再回载》
- 15 张表格全部替换为内联 CSS 图卡(层叠/介质流/状态机/映射/字段卡/placement/read-write 对照);`table=0 img=0 class=0 script=0 style 标签=0`。
- 中文标点全角、中文引号、组件字号上调、390px 预览;草稿箱两篇已原地更新,**未发布**。
- 微信流程已固化为 skill:`zhang-ruyi/skills` → `skills/wechat-article`(commit `49e691b`)。

### fnOS 应用(ruy-fnos)

- 把博客 + 两个图集打包成飞牛原生应用 `RUY 知识库`,已安装运行在 `192.168.5.53`,端口 `8899`。
- 形态:原生应用(端口服务),`cmd/main` 起 `python3 -m http.server`,`ctl_stop=true`、`service_port=8899`。
- 内容:19 个博客页面 + 58 张 Linux 图 + 7 张 LLM 图,离线可读;包约 15MB。
- 移动端:`tools/mobile.css` 修复文章页横向溢出(CSS Grid `1fr` 被内容撑成 920px,需 `minmax(0,1fr)`)、宽图组件内部滚动、关闭滚动淡入。
- 构建:`build.sh`(Jekyll → 复制图集 → 注入 CSS/改写链接 → 版本 +1 → fnpack);部署:`deploy.sh`(卸载→安装→启动→验证)。
- 踩过的坑:
  - 飞牛不支持同 appname 覆盖安装,必须**先卸载再装**(否则版本号不变、内容不更新)。
  - CGI 入口(iframe + `/cgi/ThirdParty/<app>/index.cgi/`)在 v0.1.2 能显示图标但点击无反应;端口服务模式可用。
  - 入口 `port` 与 manifest `service_port` 必须一致;给入口硬写系统端口 5666 会导致图标消失。
- 仓库状态:工程在 `~/opencode/workspace/ruy-fnos`,**尚未建 git 仓库/推送**。

### Skills

| Skill | 状态 |
|---|---|
| `kernel-diagrams` | 已归档 |
| `layout-map` | 已归档 |
| `tree-map` | 已归档 |
| `wechat-article` | 已归档并推送 |

### 本地工具

| 工具 | 路径 | 用途 |
|---|---|---|
| `clash-doctor` | `~/opencode/workspace/clash-doctor` | 软路由代理体检:模式/节点/规则/出口实测 + 修复指南;支持 `--sub` 订阅校验、`--oc` SSH/UCI 配置层、`--fix` 自动修复、`--watch`;凭证 `~/.config/opencode/clash.env` |
| `ruy-fnos` | `~/opencode/workspace/ruy-fnos` | 博客 → 飞牛 fnOS 应用;`build.sh` 打包、`FNOS_PW=... ./deploy.sh` 构建并部署 |
| `daily-digest` | `~/opencode/workspace/daily-digest` | 每日新闻推送(AI 08:00 / 内核 12:00 / 半导体 17:00),企微机器人;路由 cron 运行,日志 `/var/log/daily-digest.log` |

## 5. 接下来

1. **内核证据校验脚本**:写 `verify_sources.py`,用 `git show <revision>:<path>` 校验 `.archify/*/candidate.json` 的 `sources` 与卡片 `函数 — path:line`;修掉审计发现的 3 条卡片偏差(startup_64、dev 误解析、__napi_poll)与 `workflow-concurrency-primitives` 缺失的 `meta.repository`。
2. **ruy-fnos 归档**:工程尚未建 git 仓库;确认后推送到 `zhang-ruyi/ruy-fnos`(或并入其他仓库)。
3. **微信草稿**:用户在后台预览两篇草稿;确认手机端渲染后手动群发。若某组件仍挤/断行,只调该组件的内联样式并 `draft/update`,不新建草稿。
4. **Skill 同步(可选)**:把 `wechat-article` 复制到项目 `.opencode/skills/` 或全局,便于下次直接触发。
5. **博客同步(可选)**:把微信版文字/图卡改动回灌到 `_posts/*.md`,保持网页与公众号一致。
6. **图集继续**:按需补图/修图;改动必须重跑四门禁并做浏览器检查。图集更新后需重跑 `ruy-fnos/build.sh`。
7. **GitHub**:`gh` token 已失效;仓库操作用 SSH。新建仓库需用户手动或重新登录 `gh`。
8. **工具沉淀**:把新出现的稳定模式(layout-map/tree-map/dataflow)继续归档到 `zhang-ruyi/skills`。

## 6. 开发约束(必须遵守)

### 6.1 Archify

- 四门禁必须全 pass:`validate` / `deliver` / `check` / `browser-check`。
- 环境变量:
  ```bash
  export ARCHIFY_CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
  export ARCHIFY_CHROME_NO_SANDBOX=1
  ```
- 修改已有候选后重跑 finalize,**必须**加新输出目录:
  `.archify/<dir>/review-<N>`,避免 lock 冲突。
- 并发 finalize 会 `delivery/concurrent-attempt` 失败;串行重试,不要并行。
- 图内符号/行号必须 `grep -n` / `rg -n` 核实;版本标签、`meta.repository.url` 与真实 origin 一致。
- Linux 与 LLM 图集 UI 必须区分:Linux=Blueprint Console;LLM=Bento。不要把两套风格混用。

### 6.2 微信文章

- 微信剥离 `<style>`、`class`、`<script>`、`<iframe>`;所有样式**逐元素内联**。
- 数据视图**不要** `<table>`;用卡片/流向/字段卡;字段清单不要做成“无边框两列表格”。
- 正文 16px/1.8;组件说明 ≥12.5px;标签/ pill ≥11px;H2 20px、H1 24px。
- 中文正文全角标点、中文引号;代码/URL 保持 ASCII;短代码 `white-space:nowrap`,避免 `bi_vc/nt`。
- 390px 宽度预览;检查横向溢出、标题孤字、代码断词、箭头吊行尾。
- 只调用草稿接口(`draft/add` / `draft/update`),**绝不自动群发**。用户后台预览确认后才发布。
- `draft/add` 的 `articles` 是数组;`draft/update` 的 `articles` 是对象(写错 `47001`)。
- 封面必须永久素材 media_id;正文 H1 不放进 `content`,标题走 `title` 字段。
- `content_source_url` 必须 200;更新前 `curl --noproxy '*' -I` 验证。
- 凭证只放 `~/.config/opencode/wechat.env`(`chmod 600`);不打印 AppSecret/token;直连出口 IP 加入公众号白名单。
- 详见 `zhang-ruyi/skills` 的 `wechat-article` skill。

### 6.3 写作与图示

- 图先讲“数据形态/介质视图”,不要堆字段清单;字段说明用卡片而不是表格。
- 面板标题不要和 H2 完全重复;补充“这张图新增的信息”。
- 颜色只表示层级/介质,不表示“数据是否搬运”;文字不要写“蓝线/黄线”,除非图里确有彩色连接线。
- 调用链可保留代码块(便于复制);层级/包含用 tree-map;区间用 layout-map;决策流程优先 Archify workflow。
- 源码级断言附 `file:line`;不确定的结论宁可不写。
- 公众号版不要嵌 Archify iframe;用原生 CSS 组件或截图(截图是最后手段)。

### 6.4 Git 与安全

- 只有用户明确要求才 commit/push;小改动本地 commit,重大变更才 push。
- 提交前看 `git status` / `git diff` / `git log --oneline -10`;只 stage 预期文件。
- 不提交密钥、token、`wechat.env`、`wechat-token.json`。
- 不改 git config、不 force-push、不跳过 hooks。
- 不使用 `pkill -f`(会误杀当前 shell);查端口用 `ss -tlnp | grep ':8000'`,取 pid 再 kill。
- 代理:`192.168.5.75:7890`;微信 API 用 `trust_env=False` 直连(白名单 IP `117.22.85.159`,以实际出口为准)。浏览器访问内网时需绕代理。

### 6.5 飞牛 fnOS 应用

- 应用工程放 `~/opencode/workspace/ruy-fnos`;每次内容更新跑 `FNOS_PW=... ./deploy.sh`。
- 飞牛**不支持同 appname 覆盖安装**,必须卸载后安装;`deploy.sh` 已封装。
- 桌面入口 `port` 必须等于 manifest `service_port`;不要写系统端口(5666 等),否则图标不显示。
- 静态站用端口服务(`python3 -m http.server`),不用 CGI 入口(当前版本点击无反应)。
- 图集目录随包分发时,需把 `../diagrams/`、`../posts/`、`../` 改写成根路径(`tools/postprocess.py` 已处理)。
- 移动端改动只改 `tools/mobile.css`;改完必须用 390px 截图复核(文章页、首页、图集页)。
- `FNOS_PW` / SSH 私钥不进仓库;NAS 上 `appcenter-cli` 需 sudo。

## 7. 常用命令

### 微信文章

```bash
cd /tmp/opencode/ruy-blog
python3 wechat/build_html.py                    # 全部 md → html/
python3 wechat/build_html.py article.md --strict
```

390px 预览:

```bash
CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
$CHROME --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=390,12000 \
  --virtual-time-budget=1500 --screenshot=/tmp/opencode/preview.png \
  "file:///tmp/opencode/ruy-blog/wechat/html/article.html"
```

草稿接口:

```bash
cd /path/to/wechat-article
python3 scripts/wechat_draft.py test
python3 scripts/wechat_draft.py create --html html/a.html --cover cover.jpg --digest "摘要"
python3 scripts/wechat_draft.py update --media-id <DRAFT_ID> --html html/a.html
python3 scripts/wechat_draft.py list
```

### 飞牛 fnOS 应用

```bash
cd ~/opencode/workspace/ruy-fnos
./build.sh                                # 只打包:ruy/ruy.fpk
FNOS_PW='...' ./deploy.sh                 # 构建 + 卸载旧版 + 安装 + 启动 + 验证
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://192.168.5.53:8899/
```

移动端复核(390px):

```bash
cd ~/opencode/workspace/ruy-fnos/ruy/app/www
python3 -m http.server 8010 --bind 127.0.0.1 &
CHROME=$HOME/.cache/archify-chrome/chrome-headless-shell-linux64/chrome-headless-shell
$CHROME --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=390,1600 \
  --virtual-time-budget=1500 --screenshot=/tmp/opencode/m.png \
  http://127.0.0.1:8010/2026/11/18/io-data-journey.html
```

### 每日新闻推送(daily-digest)

```bash
cd ~/opencode/workspace/daily-digest
python3 digest.py ai                      # 立即推送
python3 digest.py kernel --dry-run        # 预览
python3 digest.py semi --hours 48 --per-source 4
ssh root@192.168.5.75 'python3 /etc/daily-digest/digest.py ai --dry-run'
```

路由器定时:`08:00 ai` / `12:00 kernel` / `17:00 semi`(`/etc/crontabs/root`);去重状态 `/etc/daily-digest/seen.json`。

### 代理体检(clash-doctor)

```bash
cd ~/opencode/workspace/clash-doctor
python3 clash_doctor.py                    # 体检
python3 clash_doctor.py --fix --yes        # 运行时修复
python3 clash_doctor.py --sub '<订阅URL>'    # 订阅格式/UA 校验
python3 clash_doctor.py --oc status        # OpenClash 配置层(SSH)
python3 clash_doctor.py --watch 60         # 定时观察
```

### Jekyll

```bash
docker run --rm --entrypoint jekyll --user $(id -u):$(id -g) -e HOME=/tmp \
  -v /tmp/opencode/ruy-blog:/srv/jekyll \
  -v /tmp/opencode/_site_test:/tmp/_site \
  jekyll/jekyll:4 build --source /srv/jekyll --destination /tmp/_site
```

### 网络/服务排查

```bash
ss -tlnp | grep ':8123'
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' -L <url>
```

### Git

```bash
git status --short
git diff --stat
git push origin main
```

## 8. 故障排查

| 现象 | 处理 |
|---|---|
| Archify `delivery/concurrent-attempt` | 串行重试,换 `review-<N>` 输出目录 |
| 微信 `47001 data format error` | `draft/update` 的 `articles` 必须是对象 |
| 微信 `40164` | 出口 IP 不在白名单;确认直连 IP |
| 微信 `48001` | 账号没有草稿/素材权限 |
| 草稿标题重复 | 正文 H1 不放进 `content`;标题走 `title` |
| 代码 span 断词 | 短词 `white-space:nowrap`;长词才 `overflow-wrap` |
| 组件像表格 | 改成字段卡/流程卡,不要两列+虚线 |
| 本地预览 404/空白 | 检查 `/tmp/opencode/serve` 软链与 `_site_test`;确认端口 |
| 图片/字体加载失败 | 微信不加载外链;全部内联/上传素材 |
| 飞牛安装后版本没变 | 先 `uninstall` 再 `install`;不支持同 appname 覆盖 |
| 飞牛桌面图标消失 | 入口 `port` 必须等于 `service_port`;不要写系统端口 5666 |
| 飞牛点击「打开」无反应 | 改用端口服务模式,不用 CGI 入口 |
| 移动端文章横向溢出 | `.article-layout` 用 `minmax(0,1fr)`;`io-box` 等加 `overflow-x:auto` |

## 9. 验收清单

发布或交付前:

- [ ] 源码符号/行号已核实
- [ ] Archify 四门禁 pass;UI 风格正确
- [ ] 文章图与文字语义一致;无表格堆字段
- [ ] 微信 `table=0 img=0 class=0 script=0 style 标签=0`
- [ ] 390px 预览无溢出/断词/孤字
- [ ] 「阅读原文」链接 200
- [ ] 草稿箱预览确认;未自动发布
- [ ] fnOS 应用:文章页/首页/图集页 390px 无横向溢出;包内图集返回链接可用
- [ ] 无密钥/token 进入仓库
- [ ] commit 信息清晰,只包含预期文件
