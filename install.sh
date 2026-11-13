#!/usr/bin/env sh
# my-awesome-skills 安装（macOS / Linux）
# 用法：sh install.sh        安装到 ~/.dsh/skills
#      DSH_HOME=/path sh install.sh
set -e

REPO=$(cd "$(dirname "$0")" && pwd)
DEST="${DSH_HOME:-$HOME/.dsh}/skills"

echo "仓库：$REPO"
echo "目标：$DEST"
mkdir -p "$DEST"

count=0
for src in "$REPO"/skills/* "$REPO"/personal/*; do
    [ -f "$src/SKILL.md" ] || continue
    name=$(basename "$src")
    if [ -e "$DEST/$name" ]; then
        echo "  跳过 $name（已存在）"
        continue
    fi
    ln -s "$src" "$DEST/$name"
    echo "  安装 $name"
    count=$((count + 1))
done

echo
echo "完成：新装 $count 个。打开任意 AI 编码工具的新会话即可使用。"
echo "撤销：rm -rf \"$DEST\"/<技能名>  （只删软链，不影响仓库）"
