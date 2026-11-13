#!/usr/bin/env python3
"""扫描本仓库的技能，校验结构，并生成统筹指挥人的 L0 路由菜单。

用法：
    python scripts/scan_skills.py                 # 校验（等同 --check）
    python scripts/scan_skills.py --check --strict
    python scripts/scan_skills.py --menu           # 重算 L0 菜单并写回
    python scripts/scan_skills.py --json

零第三方依赖，Python 3.9+。
"""

from __future__ import annotations

import argparse
import json
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
ROOTS = [("skills", "global"), ("personal", "personal")]
MENU_OWNER = REPO_ROOT / "skills" / "master-orchestrator" / "SKILL.md"

MENU_BEGIN = "<!-- MENU:BEGIN -->"
MENU_END = "<!-- MENU:END -->"

L0_RED_LINE = 500

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SCOPES = {"global", "personal"}
TYPES = {"flow", "domain", "role"}
PRIORITIES = {"highest", "high", "normal"}

REQUIRED_SECTIONS = ["适用", "步骤", "检查清单", "跑偏信号", "产出"]

META_KEYS = ["version", "scope", "type", "domain", "priority", "trigger", "updated"]


# --------------------------------------------------------------------------- #
# 极简 frontmatter 解析：支持顶层标量、单层嵌套块、行内列表
# --------------------------------------------------------------------------- #
def _clean_scalar(raw: str):
    value = raw.strip()
    if value == "":
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_unquote(item.strip()) for item in inner.split(",")]
    return _unquote(value)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_frontmatter(text: str):
    """返回 (frontmatter_dict, body_lines)；没有 frontmatter 时 dict 为 None。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines

    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() in ("---", "..."):
            end = index
            break
    if end is None:
        return None, lines

    data: dict = {}
    current_nested = None
    for line in lines[1:end]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, raw_value = line.strip().partition(":")
        key = key.strip()
        if not key:
            continue
        if indent == 0:
            if raw_value.strip() == "":
                data[key] = {}
                current_nested = key
            else:
                data[key] = _clean_scalar(raw_value)
                current_nested = None
        else:
            if current_nested is None:
                continue
            nested = data.get(current_nested)
            if isinstance(nested, dict):
                nested[key] = _clean_scalar(raw_value)

    return data, lines[end + 1 :]


# --------------------------------------------------------------------------- #
# 校验
# --------------------------------------------------------------------------- #
def estimate_tokens(text: str) -> int:
    """粗估 token：CJK 记 1，其他每 3 个字符记 1。偏保守，宁可高估。"""
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    others = len([ch for ch in text if not ("\u4e00" <= ch <= "\u9fff") and not ch.isspace()])
    return cjk + (others + 2) // 3


def validate(skill_dir: Path, meta: dict, body: str, expected_scope: str, has_bom: bool = False):
    errors, warnings = [], []
    folder = skill_dir.name

    if has_bom:
        errors.append(
            "文件带 UTF-8 BOM：宿主会静默加载失败（技能看起来存在但永远不出现）。"
            "用编辑器另存为「UTF-8 无 BOM」，或 python -c 去掉 BOM。"
        )

    if meta is None:
        errors.append("缺少 frontmatter（文件必须以 --- 开头并有闭合的 ---）")
        return errors, warnings, {}

    name = str(meta.get("name", ""))
    description = str(meta.get("description", ""))
    when_to_use = str(meta.get("whenToUse", ""))
    inner = meta.get("metadata") if isinstance(meta.get("metadata"), dict) else {}

    if not name:
        errors.append("frontmatter 缺少 name")
    elif not KEBAB.match(name):
        errors.append(f"name 不是 kebab-case: {name}")
    elif name != folder:
        errors.append(f"name ({name}) 与目录名 ({folder}) 不一致")

    if not description:
        errors.append("frontmatter 缺少 description")
    else:
        if len(description) > 160:
            warnings.append(f"description 过长（{len(description)} 字），路由会变模糊")
        looks_conditional = bool(re.search(r"当.+?时", description)) or description.startswith("When")
        if not looks_conditional:
            errors.append("description 不是条件句（应写成「当……时触发」）")

    if not when_to_use:
        warnings.append("建议补 whenToUse，路由更准")

    for key in META_KEYS:
        if key not in inner or inner[key] in ("", None):
            errors.append(f"metadata 缺少 {key}")

    version = str(inner.get("version", ""))
    if version and not SEMVER.match(version):
        errors.append(f"metadata.version 不是 semver: {version}")

    scope = str(inner.get("scope", ""))
    if scope and scope not in SCOPES:
        errors.append(f"metadata.scope 非法: {scope}（应为 global 或 personal）")
    elif scope and scope != expected_scope:
        errors.append(f"metadata.scope={scope} 与所在目录不符（{skill_dir.parent.name}/ 要求 {expected_scope}）")

    if str(inner.get("type", "")) and inner.get("type") not in TYPES:
        errors.append(f"metadata.type 非法: {inner.get('type')}（应为 flow / domain / role）")

    if str(inner.get("priority", "")) and inner.get("priority") not in PRIORITIES:
        errors.append(f"metadata.priority 非法: {inner.get('priority')}（应为 highest / high / normal）")

    domain = str(inner.get("domain", ""))
    if domain and not KEBAB.match(domain):
        errors.append(f"metadata.domain 不是 kebab-case: {domain}")

    trigger = inner.get("trigger", "")
    if isinstance(trigger, list):
        if not trigger:
            errors.append("metadata.trigger 为空")
    elif not str(trigger).strip():
        errors.append("metadata.trigger 为空")

    updated = str(inner.get("updated", ""))
    if updated and not ISO_DATE.match(updated):
        errors.append(f"metadata.updated 不是 YYYY-MM-DD: {updated}")

    if not re.search(r"^#\s+\S", body, flags=re.MULTILINE):
        errors.append("正文缺少一级标题（# 标题）")

    headings = re.findall(r"^##\s+(.+)$", body, flags=re.MULTILINE)
    joined = "\n".join(headings)
    for section in REQUIRED_SECTIONS:
        if section not in joined:
            errors.append(f"正文缺少段落：## …{section}…")

    return errors, warnings, inner


def discover():
    skills = []
    for root_name, expected_scope in ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            raw = skill_md.read_bytes()
            has_bom = raw.startswith(b"\xef\xbb\xbf")
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("utf-8", errors="replace")
            meta, body_lines = split_frontmatter(text)
            body = "\n".join(body_lines)
            errors, warnings, inner = validate(skill_dir, meta, body, expected_scope, has_bom)
            skills.append(
                {
                    "dir": skill_dir,
                    "path": skill_md,
                    "root": root_name,
                    "name": (meta or {}).get("name", skill_dir.name),
                    "domain": str(inner.get("domain", "?")),
                    "scope": str(inner.get("scope", "?")),
                    "type": str(inner.get("type", "?")),
                    "priority": str(inner.get("priority", "?")),
                    "version": str(inner.get("version", "?")),
                    "errors": errors,
                    "warnings": warnings,
                }
            )

    names = {}
    for item in skills:
        names.setdefault(item["name"], []).append(item)
    for name, group in names.items():
        if len(group) > 1:
            where = " / ".join(str(g["path"].parent) for g in group)
            for item in group:
                item["errors"].append(f"技能名重复：{name}（{where}）")

    return skills


def build_menu(skills):
    lines = []
    for item in sorted(skills, key=lambda s: (s["scope"] != "global", s["domain"], s["name"])):
        if item["name"] == "master-orchestrator":
            continue
        suffix = " · personal" if item["scope"] == "personal" else ""
        lines.append(f"- {item['name']} · {item['domain']}{suffix}")
    return lines


def write_menu(lines):
    if not MENU_OWNER.is_file():
        return False, "找不到 skills/master-orchestrator/SKILL.md"
    text = MENU_OWNER.read_text(encoding="utf-8")
    if MENU_BEGIN not in text or MENU_END not in text:
        return False, "SKILL.md 里缺少 MENU:BEGIN / MENU:END 标记"

    head, _, rest = text.partition(MENU_BEGIN)
    _, _, tail = rest.partition(MENU_END)
    block = MENU_BEGIN + "\n" + "\n".join(lines) + "\n" + MENU_END
    # newline="\n" 很关键：Windows 默认会把 \n 翻成 \r\n，导致每次 --menu 都产生无意义的 diff
    with open(MENU_OWNER, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(head + block + tail)
    return True, "已写回 " + str(MENU_OWNER.relative_to(REPO_ROOT))


def main():
    parser = argparse.ArgumentParser(description="校验技能并生成 L0 路由菜单")
    parser.add_argument("--check", action="store_true", help="只校验（默认行为）")
    parser.add_argument("--strict", action="store_true", help="把警告也当作错误")
    parser.add_argument("--menu", action="store_true", help="重算 L0 菜单并写回指挥人 SKILL.md")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args()

    skills = discover()
    total_errors = sum(len(s["errors"]) for s in skills)
    total_warnings = sum(len(s["warnings"]) for s in skills)

    menu_lines = build_menu(skills)
    menu_text = "\n".join(menu_lines)
    menu_tokens = estimate_tokens(menu_text)

    if args.menu:
        ok, message = write_menu(menu_lines)
        if args.json:
            pass
        else:
            print(("[menu] " + message) if ok else ("[menu][FAIL] " + message))

    if args.json:
        print(
            json.dumps(
                {
                    "skills": [
                        {
                            "name": s["name"],
                            "root": s["root"],
                            "domain": s["domain"],
                            "scope": s["scope"],
                            "type": s["type"],
                            "priority": s["priority"],
                            "version": s["version"],
                            "errors": s["errors"],
                            "warnings": s["warnings"],
                        }
                        for s in skills
                    ],
                    "menu_tokens": menu_tokens,
                    "errors": total_errors,
                    "warnings": total_warnings,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"发现技能 {len(skills)} 个（skills/ 与 personal/）\n")
        header = f"{'技能':<32}{'域':<12}{'类型':<7}{'范围':<10}{'版本':<8}"
        print(header)
        print("-" * len(header))
        for s in skills:
            print(f"{s['name']:<32}{s['domain']:<12}{s['type']:<7}{s['scope']:<10}{s['version']:<8}")

        if total_errors or total_warnings:
            print()
        for s in skills:
            for err in s["errors"]:
                print(f"[ERROR] {s['name']}: {err}")
            for warn in s["warnings"]:
                print(f"[WARN ] {s['name']}: {warn}")

        print()
        print(f"L0 菜单：{len(menu_lines)} 条 · 约 {menu_tokens} token（红线 {L0_RED_LINE}）")
        if menu_tokens > L0_RED_LINE:
            total_errors += 1
            print(f"[ERROR] L0 菜单超过红线 {L0_RED_LINE} token，请合并技能而不是调高红线")

    if total_warnings and args.strict:
        total_errors += total_warnings

    print()
    if total_errors:
        print(f"结果：{total_errors} 个问题（--strict 下警告也计入）")
        return 1
    print("结果：全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
