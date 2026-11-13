# 开源发布

自用跑通之后才走这里。**顺序不能颠倒，第一道没洗干净的仓库永远不该推上去。**

## 第一道：机器洗（自动脱敏）

```bash
python scripts/desensitize.py --check .     # 必须 0 命中
```

覆盖项：密钥/令牌、内网 IP、内网域名、绝对路径、邮箱、手机号、疑似客户名占位。

有命中就修，不要加豁免。`skills/` 下出现豁免注释会被脚本直接判失败——这是故意的。

## 第二道：人工洗（业务黑话）

跑一遍：

```bash
git ls-files | grep -v '^personal/'
```

逐个文件问三个问题：

1. 这里的业务口径（税率、结算规则、审批流、内部系统代号）是不是只有我们公司懂？
   - 是 → 移到 `personal/`，不要开源。
2. 这里的例子是不是能反推出真实客户/真实数据规模？
   - 是 → 换成 `<CUSTOMER>`、`<ID>` 之类的占位符。
3. 这里的"经验"是不是只对某一家公司的组织架构成立？
   - 是 → 抽象成条件句，或者干脆不要。

判定口径：**公开区只放"任何团队都能直接用"的通用能力**。领域知识是私有资产。

## 第三道：历史洗（Git 历史）

```bash
git log --all --oneline -- personal | head
```

- 有任何输出 → 说明 `personal/` 曾经被提交过。此时**不要** revert，那没有用，历史还在。
  正确做法：`git filter-repo --path personal/ --invert-paths`（或直接用干净目录重新 `git init`）。
- 确认干净之后，才能推。

`.gitignore` 已排除 `personal/`，所以正常流程下这一步应该是空的。跑它只是为了确认"正常"。

---

## 贡献三问（别人提 PR 时用）

一个外部技能要合进 `skills/`，必须三问全过：

1. **可复用吗**：换一个项目、换一个团队，这套步骤还成立吗？
2. **可执行吗**：正文是"照着能做的步骤"，还是"读完有道理的说明"？
3. **无泄漏吗**：有没有客户名、内网地址、真实 ID、业务口径？有没有 `scope: personal` 却想合进公开区？

只过两问 → 退回。这是唯一的评审标准，不设其他门槛。

## 发布到 npm（第二条分发通道）

和 ponytail 保持一致：仓库本身既是插件市场，也是一个 npm 包。

```bash
# 1) 先看一眼会被打进去什么（这一步必须做，`personal/` 绝不能进包）
npm pack --dry-run

# 2) 登录（一次即可，token 存在你机器上）
npm login

# 3) 发布
npm publish --access public
```

包内容由 `package.json` 的 `files` 白名单决定，当前只含：
`skills/`、`plugin.json`、`.claude-plugin/`、`AGENTS.md`、`README.md`、`LICENSE`、`scripts/cli.js`。
`personal/`、`docs/`、`examples/` 都不在名单里——这是刻意的。

### 版本号规则

| 变更 | 命令 |
|---|---|
| 加技能 / 改引擎行为 | `npm version minor && git push --follow-tags` |
| 改字段 / 破坏兼容 | `npm version major && git push --follow-tags` |
| 改错别字 | `npm version patch && git push --follow-tags` |

**三处版本号要保持一致**：`package.json`、`plugin.json`、`.claude-plugin/plugin.json`。
发版前跑一次下面的检查：

```bash
node -e "const f=require('fs');const v=['package.json','plugin.json','.claude-plugin/plugin.json'].map(p=>JSON.parse(f.readFileSync(p)).version);console.log(v, new Set(v).size===1?'一致':'不一致')"
```

### 如果包名被占用

`my-awesome-skills` 很可能已经有人注册。改成作用域包（推荐，和 ponytail 的
`@dietrichgebert/ponytail` 同一种做法）：

```bash
npm init --scope=@yaojiehua-miraculous   # 会改成 @yaojiehua-miraculous/my-awesome-skills
npm publish --access public
```

作用域名 = 你的 npm 用户名时不需要额外建组织。

---

## 打标签与发布

```bash
python scripts/scan_skills.py --menu --strict    # 全绿
python scripts/desensitize.py --check .
git add -A && git commit -m "chore: v1.0.0"
git tag -a v1.0.0 -m "v1.0.0 初版：引擎 + 5 份种子 + 3 份黄金示例"
git push origin main --tags
```

## README 里必须写清的四句话

开源一套"方法论"最容易出的问题是被误读成"下载即获得作者的经验"。所以 README 开头必须写：

1. 开源的是**引擎和种子**，不是我的积累。
2. 真正的资产是你自己 `personal/` 里长出来的东西。
3. `personal/` 永不提交，这是设计，不是疏忽。
4. 想分享你的技能，走贡献三问，别直接 PR 你的私有目录。

## 发布之后

- 不要在 README 里堆"我们支持 N 个平台"——只写实测过的，其他写"未验证"。
- 收 issue 时优先问"你的 `personal/` 里现在有几个技能"——这个数字比任何反馈都能说明问题。
- 版本号规则：技能新增 = minor；引擎行为变化 = minor；破坏性字段变更 = major。
