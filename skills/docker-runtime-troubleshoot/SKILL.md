---
name: docker-runtime-troubleshoot
description: 当容器起不来、端口不通、镜像拉取超时、容器内连不上外网或挂载目录为空时触发，用于按镜像/网络/卷/权限四层排查，而不是重装 Docker。
whenToUse: 用户报 Docker 或 Compose 的运行时故障，且还没确认问题属于镜像、网络、卷挂载还是权限。
metadata:
  version: 1.0.0
  scope: global
  type: flow
  domain: devops
  priority: normal
  trigger: docker|容器|compose|镜像拉取|端口不通|挂载|exited|unhealthy
  updated: 2026-11-13
---

# 容器运行时排查

容器出问题时的第一反应通常是"重启一下"。这份流程的作用是让你在重启之前就知道答案。

## 适用 / 不适用

**适用**：容器启动即退出、端口访问不通、镜像拉取卡住、挂载目录为空、容器内无外网。
**不适用**：构建阶段失败（Dockerfile 语法、构建缓存）——那是构建问题，不是运行时。

## 步骤

**Step 1 看状态，不看日志**
```
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```
先区分四种形态：`Exited (0)` / `Exited (非0)` / `Up` 但 `unhealthy` / `Restarting` 循环。
每种形态下一步完全不同，不要跳过。

**Step 2 按形态分流**

| 形态 | 首要怀疑 | 第一条命令 |
|---|---|---|
| Exited (0) 立刻退出 | 主进程不是前台运行 | `docker logs --tail 50 <name>` |
| Exited (非0) | 启动期异常（配置/依赖/权限） | `docker logs --tail 200 <name>` |
| Up 但不通 | 端口映射或监听地址 | `docker port <name>` + `ss -lntp` |
| Restarting 循环 | 探针失败或进程崩溃 | `docker inspect -f '{{.State.ExitCode}}' <name>` |
| 拉取超时 | 镜像源 / DNS / 代理 | `docker pull <image>` 单独跑一次 |

**Step 3 进容器取证**（仅在需要时）
```
docker exec -it <name> sh -c 'id; ls -la /挂载点; cat /etc/resolv.conf'
```
三件事一起看：当前用户、挂载点内容、DNS 配置。挂载为空九成是宿主机路径不存在或用了相对路径。

**Step 4 网络单独验**
容器内无外网 ≠ 宿主机无外网。分开验：
- 宿主机：`curl -I https://<目标>`
- 容器内：`docker exec <name> wget -qO- http://<目标>`
- 两者不一致 → 查 `--network` 模式与 DNS，不要动宿主机网络。

**Step 5 给最小修复**
优先顺序：改 Compose 配置 > 改启动参数 > 改镜像。重装 Docker 是最后一步，且需要证据支持（如 `dockerd` 自身日志报错）。

## 检查清单

- [ ] 先看了 `docker ps -a` 的形态，再决定查什么。
- [ ] 读过容器日志的尾部，不是只看"exited"。
- [ ] 挂载问题确认过宿主机路径存在（`ls` 过）。
- [ ] 网络问题区分了宿主机与容器两个视角。
- [ ] 修复后跑过一次 `docker ps` 确认 `Up` 且健康。

## 跑偏信号

1. 直接 `docker system prune -a`（数据没了，问题还在）。
2. 只看 `docker logs` 第一行就下结论。
3. 用 `--privileged` 当万能药。
4. 挂载为空却去查镜像。
5. 把"容器内没网"当成"服务器没网"。

## 产出

```
形态：Exited(1) / Up-unhealthy / ...
根因：<一句话>
最小修复：<配置或命令>
验证：docker ps 显示 Up (healthy)
```
