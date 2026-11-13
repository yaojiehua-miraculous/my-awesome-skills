# 加载手册：在各家 AI Coding 工具里用上这套技能

给"不想看命令行、不想读文档"的人写的手册。**先做三步自测，再按表装**——因为各家工具对 `SKILL.md` 的支持不一样，猜不如测。

---

## 第 0 步：三步自测（两分钟，决定后面怎么装）

不同工具、不同版本差异很大，别信任何人（包括这份文档）的口头结论，自己测一次：

**① 在项目根建一个测试技能**（复制粘贴即可）

```
<你的项目>/.agents/skills/zz-test/SKILL.md
```

```markdown
---
name: zz-test
description: 当用户说"测试技能是否加载"时触发。
---

# 测试技能

如果你能读到这段文字，说明技能加载成功。
```

**② 新开一个会话**，在输入框敲 `/`，看列表里有没有 `zz-test`。

**③ 按结果分流**

| 结果 | 结论 | 下一步 |
|---|---|---|
| 出现了 | 这个工具认 `SKILL.md`，`.agents/skills` 可用 | 按「装法」表安装 |
| 没出现 | 换 `.cursor/skills/` 再试一次 | 还是没有 → 走最后的「降级方案」 |

> 会话必须**新开**。已经开着的会话不会重新扫描目录。

---

## 谁认 `SKILL.md`（这张表决定装到哪）

| 目录 | DSH | Cursor | Claude Code | Codex |
|---|---|---|---|---|
| `.dsh/skills/`（项目）· `~/.dsh/skills/` | ✅ **本机实测** | — | — | — |
| `.agents/skills/`（项目）· `~/.agents/skills/` | ✅ 实现里有此扫描根 | ✅ 官方文档 | — | — |
| `.cursor/skills/`（项目）· `~/.cursor/skills/` | — | ✅ 官方文档 | — | — |
| `.claude/skills/`（项目）· `~/.claude/skills/` | — | ✅ 官方文档（兼容读取） | ✅ 官方文档 | — |
| `.codex/skills/`（项目）· `~/.codex/skills/` | — | ✅ 官方文档（兼容读取） | — | 按官方约定 |

**证据等级**（重要，别被含糊话术骗）：
- DSH 一行：**一手**，我读了它本机的加载实现（扫描根、frontmatter 白名单、嵌套目录不发现、改完下个模型步骤生效）。
- Cursor 一行：**一手**，来自 [Agent Skills 官方文档](https://cursor.com/docs/skills)，里面明确列出目录表，并写明它会兼容读取 Claude / Codex 的目录。
- Claude Code、Codex 两行：**二手**，由 Cursor 的兼容目录列表反推，我**没有**在装有这两款工具的机器上实测。

**由此得出一个实用结论**：

- 想让 **DSH + Cursor 共用一份** → 装 `~/.agents/skills`
- 想让 **Cursor + Claude Code 共用一份** → 装 `~/.claude/skills`
- 只想要本项目生效且不污染全局 → 装项目的 `.agents/skills`（两者都认，零副作用）

---

## 装法（按"动手量"从少到多）

### ① 什么命令都不想敲：双击 `install.cmd`

**适用**：DeepSeek Harness（本机已实测）。
**装到**：`~/.dsh/skills`，全局生效，换项目也在。
**撤销**：双击 `uninstall.cmd`。

缺点：只覆盖 DSH。要 Cursor 也用，看 ②。

### ② 一条命令，装成 Cursor + DSH 共用

```powershell
# 全局（所有项目都能用，覆盖 DSH + Cursor）
python scripts\mount.py --agents-user

# 或者只在当前项目里用（不写用户目录，零副作用）
python scripts\mount.py --agents
```

需要本机有 Python。撤销：

```powershell
python scripts\mount.py --unlink --agents-user
```

### ③ 给 Claude Code 用

```powershell
python scripts\mount.py --dest %USERPROFILE%\.claude\skills
```

这一份 Cursor 也会顺带读到（它兼容 `.claude/skills`）。

### ④ 给 Codex 用

```powershell
python scripts\mount.py --dest %USERPROFILE%\.codex\skills
```

按官方目录约定写的，**未实测**。

### ⑤ 完全不装：把仓库丢进项目里

把整个 `my-awesome-skills` 目录（或它的 `.dsh` / `.agents` 子目录）放进你的项目根，
用 AI 工具**打开这个目录**，技能就在项目级目录里被扫到——不需要任何安装动作。

代价：只对这个项目生效，且仓库会占用项目磁盘空间。

---

## 只认"规则文件"的工具怎么办（降级方案）

有些工具不认 `SKILL.md`，只认一份指令文件（文件名各工具不同，常见是 `AGENTS.md`、
`.cursorrules`、`.clinerules`、`.github/copilot-instructions.md`，**具体以各工具文档为准，我没逐一验证**）。

**降级做法**：把技能正文贴进那个规则文件。

```
先把 AGENTS.md 放进去（它含五步纪律，是最有价值的部分）
再把最常用的 1–2 个 SKILL.md 的「步骤」段贴进去
```

**必须知道的代价**——这是降级，不是等价：

| | 认 SKILL.md | 只认规则文件 |
|---|---|---|
| 加载方式 | 按需加载，命中才读正文 | **全量常驻**，每轮都占上下文 |
| 技能多了以后 | 只多几行菜单 | 上下文被撑爆，模型注意力下降 |
| 路由 | `description` 语义匹配 | 靠模型自己从长文里找 |

所以降级只适合"我只想用 1–2 个技能"的人。要装 10 个以上，必须用支持 `SKILL.md` 的工具。

---

## 常见故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| 装了但列表里没有 | 文件带 UTF-8 BOM | 另存为 UTF-8 **无 BOM**；跑 `python scripts\scan_skills.py` 会直接报这个错 |
| 装了但列表里没有 | 技能目录被嵌套了 | 必须是 `<根>/<技能名>/SKILL.md`，中间不能再套一层（`skills/domain/xxx/SKILL.md` 不生效） |
| 装了但列表里没有 | 会话是旧开的 | 新开会话 |
| 装了但列表里没有 | 挂错位置 | 用第 0 步的三步自测确认该工具读哪个目录 |
| 列表里有，但不触发 | `description` 写成了功能介绍 | 改成「当……时触发」，跑 `scan_skills.py --menu` 刷新菜单 |
| 触发了但没按五段执行 | 只拿到摘要没拿到正文 | 显式调用一次 `/技能名`，确认正文可达 |
| 技能多开会话变慢 | 有人一次性全量读了 frontmatter | 违反红线，回到 `AGENTS.md` 的五步纪律 |
| 换了电脑就没了 | 用户级装的是**链接**，不是副本 | 新机器上重新双击 `install.cmd` 或跑 ② |

---

## 一句话总结

- **DSH**：双击 `install.cmd`，结束。
- **Cursor**：`python scripts\mount.py --agents-user`，结束。
- **两个都要**：上面两条都做，互不干扰。
- **Claude Code / Codex**：换成对应的 `--dest`，后者我未实测。
- **只认规则的老工具**：贴 `AGENTS.md`，但只适合 1–2 个技能。

---

## 出处

- Cursor 的目录表与兼容目录：[Agent Skills | Cursor Docs](https://cursor.com/docs/skills)
- Claude Code 技能机制：[Extend agents with skills](https://code.claude.com/docs/en/agent-sdk/skills)（页面内容我只读到导航，目录结论主要取自 Cursor 的兼容列表）
- DSH：读本机加载实现的结论，写在 [`ARCHITECTURE.md`](ARCHITECTURE.md) 的「宿主兼容性」一节
