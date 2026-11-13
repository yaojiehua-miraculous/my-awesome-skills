#!/usr/bin/env python3
"""把仓库里的技能挂载到宿主工具的技能目录。

默认用「目录联接 / 软链」，所以仓库里改了技能正文，宿主立刻生效，不需要重新挂。
Windows 用 junction（免管理员权限），Linux/macOS 用 symlink；两者都失败时回退为复制。

用法：
    python scripts/mount.py                          # 挂到 <仓库>/.dsh/skills（仅本目录生效）
    python scripts/mount.py --user                    # 挂到 ~/.dsh/skills（全局生效）
    python scripts/mount.py --dest ~/.claude/skills   # 挂到任意宿主目录
    python scripts/mount.py --only master-orchestrator --only api-error-triage
    python scripts/mount.py --copy                    # 复制而非链接
    python scripts/mount.py --unlink                  # 撤销挂载
    python scripts/mount.py --dry-run                 # 只看会做什么

零第三方依赖，Python 3.9+。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOTS = [REPO_ROOT / "skills", REPO_ROOT / "personal"]


def is_reparse_point(path: Path) -> bool:
    """判断是否为软链或 Windows junction。"""
    if path.is_symlink():
        return True
    try:
        os.readlink(path)
        return True
    except OSError:
        pass
    if os.name == "nt":
        try:
            import stat as stat_mod

            attrs = os.stat(path, follow_symlinks=False).st_file_attributes
            return bool(attrs & stat_mod.FILE_ATTRIBUTE_REPARSE_POINT)
        except (AttributeError, OSError):
            return False
    return False


def remove_mount(path: Path) -> bool:
    """只移除挂载点本身，绝不动源目录。"""
    try:
        if is_reparse_point(path):
            try:
                os.rmdir(path)          # junction / 目录软链
            except OSError:
                os.unlink(path)         # 文件软链
            return True
        if path.is_dir():
            shutil.rmtree(path)         # 复制出来的副本
            return True
        path.unlink()
        return True
    except OSError as error:
        print(f"  [FAIL ] 无法移除 {path}: {error}")
        return False


def create_link(source: Path, target: Path) -> bool:
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(source)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True
        return False
    try:
        os.symlink(source, target, target_is_directory=True)
        return True
    except OSError:
        return False


def collect_sources(only):
    items = []
    for root in SOURCE_ROOTS:
        if not root.is_dir():
            continue
        for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if not (skill_dir / "SKILL.md").is_file():
                continue
            items.append(skill_dir)
    if only:
        wanted = set(only)
        missing = wanted - {item.name for item in items}
        for name in sorted(missing):
            print(f"[WARN ] 找不到技能：{name}")
        items = [item for item in items if item.name in wanted]
    return items


def main():
    parser = argparse.ArgumentParser(description="把技能挂载到宿主工具的技能目录")
    parser.add_argument("--dest", help="目标目录（优先级最高）")
    parser.add_argument("--user", action="store_true", help="挂到用户级 ~/.dsh/skills（仅 DSH）")
    parser.add_argument("--agents", action="store_true", help="挂到项目级 .agents/skills（Cursor 与 DSH 都认）")
    parser.add_argument("--agents-user", action="store_true", help="挂到用户级 ~/.agents/skills（Cursor 与 DSH 都认）")
    parser.add_argument("--only", action="append", metavar="NAME", help="只挂载指定技能，可重复")
    parser.add_argument("--copy", action="store_true", help="复制而不是链接（链接失败时会自动回退）")
    parser.add_argument("--unlink", action="store_true", help="撤销挂载")
    parser.add_argument("--force", action="store_true", help="覆盖目标目录里同名但非挂载的内容")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不做任何修改")
    args = parser.parse_args()

    if args.dest:
        dest = Path(os.path.expanduser(args.dest)).resolve()
    elif args.agents_user:
        dest = (Path.home() / ".agents" / "skills").resolve()
    elif args.agents:
        dest = (REPO_ROOT / ".agents" / "skills").resolve()
    elif args.user:
        dest = (Path.home() / ".dsh" / "skills").resolve()
    else:
        dest = (REPO_ROOT / ".dsh" / "skills").resolve()

    sources = collect_sources(args.only)
    if not sources:
        print("没有可挂载的技能（skills/ 与 personal/ 都是空的？）")
        return 1

    print(f"源    ：{len(sources)} 个技能")
    print(f"目标  ：{dest}")
    print(f"模式  ：{'撤销' if args.unlink else ('复制' if args.copy else '链接')}{'（dry-run）' if args.dry_run else ''}")
    print()

    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    created = skipped = removed = failed = 0

    for source in sources:
        target = dest / source.name
        exists = target.exists() or is_reparse_point(target)

        if args.unlink:
            if not exists:
                print(f"  [ --  ] {source.name}: 未挂载")
                skipped += 1
                continue
            if args.dry_run:
                print(f"  [would] 移除 {target}")
                removed += 1
                continue
            if remove_mount(target):
                print(f"  [ -   ] {source.name}: 已移除挂载")
                removed += 1
            else:
                failed += 1
            continue

        if exists:
            same = False
            try:
                same = Path(os.path.realpath(target)) == Path(os.path.realpath(source))
            except OSError:
                same = False
            if same and not args.copy:
                print(f"  [ ok  ] {source.name}: 已挂载且指向正确")
                skipped += 1
                continue
            if not is_reparse_point(target) and not args.force:
                print(f"  [skip ] {source.name}: 目标是真实目录，未覆盖（加 --force 覆盖）")
                skipped += 1
                continue
            if args.dry_run:
                print(f"  [would] 重建 {target}")
                created += 1
                continue
            remove_mount(target)

        if args.dry_run:
            print(f"  [would] 挂载 {source.name} -> {target}")
            created += 1
            continue

        ok = False
        if not args.copy:
            ok = create_link(source, target)
            if not ok:
                print(f"  [note ] {source.name}: 链接失败，回退为复制")
        if not ok:
            try:
                shutil.copytree(source, target)
                ok = True
            except OSError as error:
                print(f"  [FAIL ] {source.name}: {error}")

        if ok and (target / "SKILL.md").is_file():
            print(f"  [ +   ] {source.name}: 已挂载")
            created += 1
        elif ok:
            print(f"  [warn ] {source.name}: 挂载完成但找不到 SKILL.md")
            created += 1
        else:
            failed += 1

    print()
    verb = "移除" if args.unlink else "挂载"
    print(f"汇总：{verb} {created if not args.unlink else removed} 个 · 跳过 {skipped} 个 · 失败 {failed} 个")

    if failed:
        return 1

    if not args.unlink and not args.dry_run:
        print()
        print("下一步：")
        print("  1) python scripts/scan_skills.py --menu      # 刷新 L0 菜单（新增技能后必跑）")
        print("  2) 在目标目录里打开你的 AI 编码工具，问一句模糊的真实问题")
        print("  3) 如果第一段不是【路由】结论 → 技能没被读到，回来看 README 的挂载表")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
