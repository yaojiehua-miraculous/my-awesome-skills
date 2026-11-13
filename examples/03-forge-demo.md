<!-- desensitize:allow-fake-secrets reason="演示脱敏前的原始脏数据，全部是伪造值，不含真实凭据" -->

# 03 · 归档示例：从脏对话到一条技能

这份示例演示 `skill-forge` 最难也最关键的一段：**把一次真实对话压成一条技能，且不带出任何敏感信息**。

下面第一段的原始对话里，故意埋了六类必须清洗的东西。数一数，你能全部找出来吗？

---

## 一、原始对话（脏数据，故意不干净）

```
用户：我们星辰零售的单据同步一直失败，报 Connection refused
助手：看了下，是 10.20.30.40:6379 那个 Redis 连不上
用户：对，内网 redis.prod.xc-internal.local 这台
助手：你试下 redis-cli -h 10.20.30.40 -p 6379 ping
用户：通了，但是同步服务还是起不来，日志里 401
助手：那看下配置里的令牌，是不是过期了
用户：D:\work\retail-sync\config\app.yml 里写着 Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.FAKE.fake-signature
助手：这个 token 过期了，去换一个。另外 B20261112-8842 这批单据卡在队列里了，要重放
用户：换了 token 之后同步正常了，B20261112-8842 重放也成功了
助手：那这类问题的根因链路是：凭据过期 → 同步服务 401 → 单据积压在队列
```

### 六类必须清洗的东西

| # | 原文片段 | 类型 |
|---|---|---|
| 1 | 星辰零售 | 客户名 |
| 2 | redis.prod.xc-internal.local | 内网域名 |
| 3 | 10.20.30.40:6379 | 内网 IP + 端口 |
| 4 | Bearer eyJ...fake-signature | 令牌 |
| 5 | D:\work\retail-sync\config\app.yml | 本地绝对路径 |
| 6 | B20261112-8842 | 可反推的真实批次号 |

只要有一个没换掉，这条技能就永久污染了公开区——而且是**永久**，因为 Git 历史会一直留着它。

---

## 二、脱敏映射

| 类型 | 占位符 | 应用后 |
|---|---|---|
| 客户名 | `<CUSTOMER>` | 客户 `<CUSTOMER>` 的单据同步 |
| 内网域名 | `<HOST>` | `<HOST>` 这台 |
| 内网 IP:端口 | `<IP>:<PORT>` | `<IP>:<PORT>` |
| 令牌 | `<SECRET>` | `Authorization: Bearer <SECRET>` |
| 本地路径 | `<PATH>` | `<PATH>` |
| 批次号 | `<ID>` | 批次 `<ID>` 卡在队列 |

**替换完立刻复检**：`python scripts/desensitize.py --check personal/`，必须 0 命中。
"我觉得没有敏感信息"不是证据，脚本输出才是。

---

## 三、三字段压缩

| 字段 | 内容 |
|---|---|
| 痛点 | 同步服务启动即退出，日志报连接下游失败或 401 |
| 方案 | 先验连通性（`redis-cli ping`）→ 通则查凭据 → 换凭据 → 重放积压队列 |
| 坑 | "连接失败"和"凭据失效"是两个不同楼层，一起改会互相掩盖 |

注意：**丢了什么**。原始对话里的客户名、具体主机、具体批次号全丢了。丢掉的不影响可执行性，
留下才是事故。

---

## 四、查重（这一步决定要不要新建文件）

看 `domain: data-sync` 下已有的技能：

```
- data-sync-connectivity · data-sync（personal）
```

打开比一下「痛点」：

- 已有技能 `data-sync-connectivity` 覆盖的是"连不上下游"这一族。
- 本次的结论是"连上了，但凭据过期导致 401"——属于**同一族的第二种成因**。

→ **判定：不新建文件。** 给 `data-sync-connectivity` 加一节「凭据失效」，`version` 从 `1.0.0` 升到 `1.1.0`。

如果这里新建了 `data-sync-auth-401`，下一次再遇到"超时"，就会出现第三个文件……
半年后你会有 30 个长得差不多的技能，路由准确率反而下降。这就是"技能库增殖 = 复利失败"。

---

## 五、落盘结果（升级后的片段）

```markdown
## 步骤

**Step 1 验连通性**
`redis-cli -h <IP> -p <PORT> ping`，返回 PONG 说明网络层没问题，进 Step 2。

**Step 2 验凭据**
读配置里 `Authorization: Bearer <SECRET>` 的签发时间。过期 → 换新凭据，进 Step 3。

**Step 3 清积压**
凭据修复后，队列里卡住的批次（如 `<ID>`）需要显式重放，服务不会自动重试。

> 注意：连通性失败与凭据失效是两个不同楼层。先验连通性，再看凭据，
> 否则会把 401 误判成网络问题。
```

`metadata.version` → `1.1.0`，`metadata.updated` → 当天日期。

---

## 六、收尾

```
归档 data-sync-connectivity v1.1.0 ← 新增「凭据过期 → 401 → 积压」成因
菜单刷新：12 个技能 · L0 约 78 token
```

最后跑一次 `python scripts/scan_skills.py --menu`，否则新技能不会被路由到——
这一步忘了，等于白干。
