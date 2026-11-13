# my-awesome-skills

**一套让「每个人自己的经验」产生复利的极简 AI 技能引擎。**

它不是技能合集，也不是给人看的文档库。它是一台发动机：装上之后，你踩过的坑会在下一次自动变成 AI 的默认行为，而这份积累永远归你、跟着你走、换工具也带得走。

---

## 一句话说清它是什么

| | 是 | 不是 |
|---|---|---|
| 定位 | 一套**进化引擎**（路由 + 降级 + 归档 + 分发） | 一包提示词 / 一个大而全的技能市场 |
| 资产归属 | 每个人各自的 `personal/`，永不上传 | 作者的经验仓库，供人下载 |
| 依赖 | 纯 Markdown + 可选 Python；零服务、零数据库 | 需要部署网关、向量库、插件 SDK |
| 生效方式 | 宿主原生 skill 机制按需加载（渐进式） | 一次性把所有规则塞进系统提示词 |

开源出去的是**发动机和种子包**，不是我的积累。真正的资产是你自己长出来的那部分。

---

## 三层结构（30 秒看懂）

```
skills/    ← 公开的通用能力：引擎本体 + 种子 SOP（会提交到 Git）
personal/  ← 你自己的经验（.gitignore 已排除，永不上传）
scripts/   ← 三个零依赖脚本：路由菜单生成与校验 / 脱敏 / 挂载
```

核心机制只有三句话：

1. **路由不写代码**：`SKILL.md` 的 frontmatter 就是路由表，助手启动时只看菜单（L0：名称 + 域），命中才读正文。
2. **三级降级**：现成生态技能 → 你的 `personal/` → 通用能力兜底。
3. **兜底成功必须归档**：这次靠通用能力解决的，下一次必须能命中一条你已有的技能。这是复利唯一的发生点。

---

## 30 秒上手

先看你是哪一类，再决定要不要自己动手：

| 你的情况 | 要不要自己动手 | 怎么装 |
|---|---|---|
| 用 DSH / Cursor，且 AI 能跑终端 | **不用，说一句话** | 见 ① |
| 用 DSH，想要最省事 | 双击一次 | 见 ② |
| 用 Claude Code / Codex | 打两条斜杠命令 | 见 ④ |
| 装到所有工具、或换系统 | 一条命令 | 见 ③ |
| 只在这个仓库里用 | 零动作 | 见 ⑤ |

### ① 说一句话就装（自然语言，AI 替你执行）

在会话里直接说：

```
把这个仓库 clone 到 <你的目录>\my-awesome-skills
再把它的 skills/ 挂到我用户级技能目录
```

AI 只要有终端权限就能自己做完（DSH、Cursor 都可以）。唯一代价：目标目录在仓库外时，
会弹一次写盘授权，点同意即可。

### ② 双击就装（Windows，零命令）

打开仓库文件夹，**双击 `install.cmd`**，看到「新装 7 个」就成。

- 装到 `~/.dsh/skills`，之后任何目录、任何新会话都生效，重启工具也还在。
- 不需要管理员权限，不复制文件（改仓库立刻生效）。
- 撤销：双击 `uninstall.cmd`。macOS / Linux 用 `sh install.sh`。

### ③ 一条命令装（任意系统）

```bash
npx my-awesome-skills                  # 自动选宿主（有 ~/.dsh 用它，否则 ~/.agents）
npx my-awesome-skills --host claude    # dsh / agents / claude / codex / cursor
npx my-awesome-skills --all            # 所有宿主
npx my-awesome-skills --unlink         # 卸载
```

npm 版是**复制**技能（不是链接），好处是不依赖本仓库还在不在；想用链接加 `--link`。

### ④ 两条斜杠命令（Claude Code / Codex，自然语言装不了）

```text
/plugin marketplace add <用户名>/my-awesome-skills
/plugin install my-awesome-skills@awesome-skills
```

Codex 换成 `codex plugin marketplace add <用户名>/my-awesome-skills`。

### ⑤ 零动作：只在这个仓库里用

用 AI 工具打开仓库目录即可——技能已经在项目级目录里，不需要装。

### 开发者 / 想调参数

```bash
python scripts/scan_skills.py --menu --strict   # 校验 + 生成 L0 菜单
python scripts/mount.py                          # 仅本目录生效
python scripts/mount.py --user                   # 全局生效（= 双击 install.cmd）
python scripts/mount.py --dest ~/.claude/skills  # 挂到别的宿主
python scripts/mount.py --unlink --user          # 撤销
```

> 双击版和命令版做的是同一件事，只是前者不依赖 Python。`install.cmd` 内部是
> `scripts/install.ps1`（PowerShell，Windows 自带）。

---

## 各宿主装到哪

| 工具 | 装到这个目录 | 会话里用自然语言能装吗 | 正确的装法 |
|---|---|---|---|
| DeepSeek Harness | `~/.dsh/skills` | ✅ 能 | 说一句话让 AI 代劳；或双击 `install.cmd` |
| Cursor（与 DSH 共用一份） | `~/.agents/skills` | ✅ 能 | `npx my-awesome-skills --host agents` |
| Cursor（单独） | `~/.cursor/skills` | ✅ 能 | `npx my-awesome-skills --host cursor` |
| Claude Code | `~/.claude/skills` | ❌ **不支持** | `/plugin marketplace add <用户名>/my-awesome-skills` |
| Codex | `~/.codex/skills` | ❌ **不支持** | `codex plugin marketplace add <用户名>/my-awesome-skills` |
| 只认规则文件的工具 | 项目根 `AGENTS.md` | ❌ **不支持** | 把 `AGENTS.md` 放进项目（降级，非等价） |
| 任意宿主（npm 通道） | 由 CLI 决定 | ✅ 能 | 说「跑一下 npx my-awesome-skills」，或自己跑 |

**装不上怎么办**：直接开 issue 反馈，把工具名 + 版本 + 报错贴上去。
**逐工具的完整装法、三步自测法、故障排查 → [docs/LOADING.md](docs/LOADING.md)**（新手先看那个）

`mount.py --help` 可看全部参数。任何不确定的宿主，`--dest` 都能兜底。

**还有第四条路：当插件包用。** 仓库同时带了两套清单，覆盖两种插件标准：

| 标准 | 清单 | 谁会读 |
|---|---|---|
| [Agent Plugins 1.0](https://agent-plugins.org) | [`plugin.json`](plugin.json)（仓库根） | 支持该标准的客户端（如 Cursor） |
| Claude Code 插件 | [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) + [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) | Claude Code |

Claude Code 里可以直接给地址装：

```text
/plugin marketplace add <你的用户名>/my-awesome-skills
/plugin install my-awesome-skills@awesome-skills
```

两份清单都按官方规范写好了；**如果按上面的命令装不上，请开 issue 反馈**（附工具名 + 版本 + 报错）。
进市场另需提交审核。
DSH 没有这条路（它的插件是 npm 包，不吃 Git 地址）。

---

## 目录说明

| 路径 | 内容 |
|---|---|
| `install.cmd` / `uninstall.cmd` | 双击即装 / 双击即撤（Windows，零命令、不依赖 Python） |
| `install.sh` | macOS / Linux 版安装脚本 |
| `package.json` + `scripts/cli.js` | npm 通道：`npx my-awesome-skills`（零依赖，Node 18+） |
| [`AGENTS.md`](AGENTS.md) | 每轮必读的五步纪律（供读 `AGENTS.md` 的宿主使用） |
| `skills/master-orchestrator/` | 统筹指挥人：只做选择题、不做问答题；文件末尾就是 L0 路由菜单 |
| `skills/skill-forge/` | 采集沉淀：脏对话 → 三字段压缩 → 强制脱敏 → 查重 → 落盘回读 |
| `skills/*`（其余 5 个） | **Global 种子包**＝基础能力：接口报错分层、容器排查、代码评审、提交规范、有效单测。保证冷启动就有及格线，不是终态 |
| `personal/` | 你的私有技能，**被 .gitignore 排除** |
| [`examples/`](examples/README.md) | 三份黄金示例：合格技能长什么样、指挥人怎么派活、脏对话怎么变成技能 |
| [`docs/LOADING.md`](docs/LOADING.md) | **加载手册**：各工具装到哪、三步自测、故障排查（新手先看这个） |
| [`docs/COLD_START.md`](docs/COLD_START.md) | 冷启动三问 + 最小装载清单 |
| [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md) | F1–F7 验收指标与测量方法 |
| [`docs/RELEASE.md`](docs/RELEASE.md) | 开源前的三道清洗 + 贡献三问 |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 架构与 token 预算的推导 |

---

## 三条红线（违反即失效）

1. **单轮正文最多 2 份**。启动时全量读所有 frontmatter 或正文 = 性能事故。
2. **`personal/` 不进 Git**。`.gitignore` 已排除；提交前 `git status` 里出现 `personal/` 就是泄漏。
3. **归档先查重**。同类问题只升次版本号，禁止新建文件。宁可合并，不可增殖。

---

## 自检

```bash
python scripts/scan_skills.py --check --strict   # 结构校验（10 字段 + 五段正文）
python scripts/scan_skills.py --menu              # 重算 L0 菜单与 token 开销
python scripts/desensitize.py --check .           # 脱敏扫描（开源前必跑）
```

三个脚本零第三方依赖，Python 3.9+ 即可。

> **Windows 上的一个坑**：PowerShell 5 用 `Set-Content -Encoding utf8` 保存的 `SKILL.md` 会带 BOM，
> 宿主会**静默加载失败**——技能看着存在，但永远不出现在目录里。`scan_skills.py` 把 BOM 判为错误，
> 报错信息会直接告诉你原因。用编辑器另存为「UTF-8 无 BOM」即可。

## License

MIT，见 [LICENSE](LICENSE)。
