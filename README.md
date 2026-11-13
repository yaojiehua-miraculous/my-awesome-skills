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

### 只想在这个仓库里用：零操作

把仓库 clone 到本地，用 AI 编码工具**打开这个目录**就有技能了。
（仓库自带 `.dsh/skills` 挂载点，克隆即用，不需要任何命令。）

### 想让所有项目都能用：双击 `install.cmd`

打开仓库文件夹，**双击 `install.cmd`**。出现「新装 7 个」就是装好了。

- 不需要命令行，不需要管理员权限，不复制文件（改仓库立刻生效）。
- 装到 `~/.dsh/skills`，之后**任何目录、任何新会话**都生效，重启工具也还在。
- 撤销：双击 `uninstall.cmd`（只删链接，不动你的技能文件）。
- macOS / Linux：`sh install.sh`。

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

## 各宿主的挂载位置

| 宿主 | 技能目录 | 命令 |
|---|---|---|
| DeepSeek Harness（本项目已实测） | `<项目根>/.dsh/skills` 或 `~/.dsh/skills` | `python scripts/mount.py [--user]` |
| Claude Code 类 | `~/.claude/skills` | `python scripts/mount.py --dest ~/.claude/skills` |
| 其他支持 `SKILL.md` 的工具 | 任意目录 | `python scripts/mount.py --dest <路径>` |
| 不支持 skill 机制的工具 | —— | 把 `AGENTS.md` 作为规则文件放进项目根 |

`mount.py --help` 可看全部参数。任何不确定的宿主，`--dest` 都能兜底。

---

## 目录说明

| 路径 | 内容 |
|---|---|
| `install.cmd` / `uninstall.cmd` | 双击即装 / 双击即撤（Windows，零命令、不依赖 Python） |
| `install.sh` | macOS / Linux 版安装脚本 |
| [`AGENTS.md`](AGENTS.md) | 每轮必读的五步纪律（供读 `AGENTS.md` 的宿主使用） |
| `skills/master-orchestrator/` | 统筹指挥人：只做选择题、不做问答题；文件末尾就是 L0 路由菜单 |
| `skills/skill-forge/` | 采集沉淀：脏对话 → 三字段压缩 → 强制脱敏 → 查重 → 落盘回读 |
| `skills/*`（其余 5 个） | global 种子 SOP：接口报错分层、容器排查、代码评审、提交规范、有效单测 |
| `personal/` | 你的私有技能，**被 .gitignore 排除** |
| [`examples/`](examples/README.md) | 三份黄金示例：合格技能长什么样、指挥人怎么派活、脏对话怎么变成技能 |
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
