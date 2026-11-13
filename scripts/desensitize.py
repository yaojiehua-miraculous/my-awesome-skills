#!/usr/bin/env python3
"""脱敏检查与就地替换。

用法：
    python scripts/desensitize.py --check .          # 全仓库扫描，有命中则退出码 1
    python scripts/desensitize.py --check skills/ personal/
    python scripts/desensitize.py --fix examples/    # 就地替换为占位符

豁免：文件内出现豁免标记注释即跳过（标记写法见 examples/README.md）；
但该标记出现在 skills/ 下会被判为失败（防止给真实资产开豁免）。
本脚本自身包含该标记的字面量，所以用拼接构造，避免自我误报。

零第三方依赖，Python 3.9+。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", ".dsh", ".skills", ".claude", ".agents", "__pycache__", ".venv", "venv", "node_modules"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".docx", ".xlsx", ".pptx", ".pyc", ".woff", ".woff2"}

EXEMPT_MARK = "desensitize:" + "allow-fake-secrets"
EXEMPT_ALLOWED_ROOTS = {"examples", "docs"}

# (名称, 正则, 占位符)
RULES = [
    ("private-ip", re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"), "<IP>"),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), "<SECRET>"),
    ("bearer", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"), "Bearer <SECRET>"),
    ("api-key", re.compile(r"\b(?:sk|ak|pk|rk)[-_][A-Za-z0-9_-]{12,}"), "<SECRET>"),
    ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<SECRET>"),
    ("secret-assignment", re.compile(r"(?i)\b(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|access[_-]?token)\s*[=:]\s*[\"']?[^\s\"']{6,}"), "<SECRET>"),
    ("win-abs-path", re.compile(r"\b[A-Za-z]:\\\\?[A-Za-z0-9_.\\-]{4,}"), "<PATH>"),
    ("posix-home-path", re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/[^\s\"'`）)]{2,}"), "<PATH>"),
    ("internal-domain", re.compile(r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:internal|intranet|corp|local|lan)\b"), "<HOST>"),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
    ("cn-mobile", re.compile(r"\b1[3-9]\d{9}\b"), "<PHONE>"),
]


def iter_files(targets):
    for target in targets:
        path = Path(target)
        if not path.is_absolute():
            path = (Path.cwd() / target).resolve()
        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = [p for p in path.rglob("*") if p.is_file()]
        else:
            print(f"[WARN ] 路径不存在：{path}")
            continue
        for file in files:
            if any(part in SKIP_DIRS for part in file.parts):
                continue
            if file.suffix.lower() in SKIP_SUFFIXES:
                continue
            yield file


def relative_label(file: Path) -> str:
    try:
        return str(file.relative_to(REPO_ROOT))
    except ValueError:
        return str(file)


def is_exempt(text: str, file: Path) -> bool:
    if EXEMPT_MARK not in text:
        return False
    try:
        top = file.relative_to(REPO_ROOT).parts[0]
    except ValueError:
        return False
    return top in EXEMPT_ALLOWED_ROOTS


def scan(files, do_fix: bool):
    total_hits = 0
    bad_exempts = 0
    changed_files = 0

    for file in files:
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        label = relative_label(file)

        # 豁免注释出现在公开技能目录 → 直接失败
        if EXEMPT_MARK in text and not is_exempt(text, file):
            bad_exempts += 1
            print(f"[ERROR] {label}: 豁免注释只允许出现在 examples/ 与 docs/，此处不允许")

        if is_exempt(text, file):
            continue

        original = text
        hits = []
        for name, pattern, replacement in RULES:
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                hits.append((line_no, name, match.group(0)[:60]))

        if not hits:
            continue

        total_hits += len(hits)
        for line_no, name, snippet in sorted(hits)[:20]:
            print(f"[HIT  ] {label}:{line_no} {name} -> {snippet}")
        if len(hits) > 20:
            print(f"[HIT  ] {label}: …另有 {len(hits) - 20} 处")

        if do_fix:
            for name, pattern, replacement in RULES:
                text = pattern.sub(replacement, text)
            if text != original:
                with open(file, "w", encoding="utf-8", newline="") as handle:
                    handle.write(text)
                changed_files += 1
                print(f"[FIXED] {label}")

    return total_hits, bad_exempts, changed_files


def main():
    parser = argparse.ArgumentParser(description="敏感信息检查与脱敏")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="只检查（默认）")
    group.add_argument("--fix", action="store_true", help="就地替换为占位符")
    parser.add_argument("targets", nargs="*", default=["."], help="文件或目录，默认全仓库")
    args = parser.parse_args()

    targets = args.targets or ["."]
    files = list(iter_files(targets))
    print(f"扫描 {len(files)} 个文本文件…\n")

    total_hits, bad_exempts, changed_files = scan(files, args.fix)

    print()
    if args.fix:
        print(f"结果：命中 {total_hits} 处，已修复 {changed_files} 个文件")
        if changed_files:
            print("提示：替换后请人工复核一遍上下文，占位符可能让句子读不通。")
        return 1 if bad_exempts else 0

    if total_hits == 0 and bad_exempts == 0:
        print("结果：0 命中，可以发布")
        return 0
    print(f"结果：{total_hits} 处命中，{bad_exempts} 个非法豁免")
    print("处理：跑 --fix 替换，或改成 <CUSTOMER> / <HOST> / <SECRET> 之类的占位符。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
