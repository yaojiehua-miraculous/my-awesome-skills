# 一键安装：把 skills/ 与 personal/ 下的技能以目录联接挂到 ~/.dsh/skills
# 由 install.cmd 双击调用；也可以直接：powershell -File scripts\install.ps1

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $env:USERPROFILE '.dsh\skills'

Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  my-awesome-skills 一键安装' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host "  仓库：$repo"
Write-Host "  目标：$dest"
Write-Host '  方式：目录联接（不复制文件，改仓库即生效）'
Write-Host '================================================'
Write-Host ''

if (-not (Test-Path $dest)) {
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
}

$ok = 0; $skip = 0; $fail = 0

foreach ($rootName in @('skills', 'personal')) {
    $root = Join-Path $repo $rootName
    if (-not (Test-Path $root)) { continue }

    Get-ChildItem -Path $root -Directory | Sort-Object Name | ForEach-Object {
        $src = $_.FullName
        $name = $_.Name

        if (-not (Test-Path (Join-Path $src 'SKILL.md'))) { return }

        $target = Join-Path $dest $name
        if (Test-Path $target) {
            Write-Host "  跳过 $name（已存在）" -ForegroundColor DarkGray
            $script:skip++
            return
        }

        try {
            New-Item -ItemType Junction -Path $target -Target $src -ErrorAction Stop | Out-Null
            Write-Host "  安装 $name" -ForegroundColor Green
            $script:ok++
        }
        catch {
            Write-Host "  失败 $name（可能被安全软件拦截，或该磁盘不支持联接）" -ForegroundColor Red
            $script:fail++
        }
    }
}

Write-Host ''
Write-Host '------------------------------------------------'
Write-Host "  新装 $ok 个 · 已存在 $skip 个 · 失败 $fail 个"
Write-Host '------------------------------------------------'
Write-Host ''

if ($ok -eq 0 -and $skip -eq 0) {
    Write-Host '[警告] 一个技能都没找到，仓库结构可能不完整。' -ForegroundColor Yellow
    exit 1
}

if ($fail -gt 0) {
    Write-Host '有技能挂载失败。可以改用管理员权限运行，或改用复制模式：' -ForegroundColor Yellow
    Write-Host '  python scripts\mount.py --user --copy' -ForegroundColor Yellow
    Write-Host ''
}

Write-Host '完成。打开任意 AI 编码工具（如 DSH）的新会话即可使用，' -ForegroundColor Cyan
Write-Host '不需要重启电脑，也不需要再运行任何命令。' -ForegroundColor Cyan
Write-Host ''
Write-Host '想撤销：双击 uninstall.cmd'
exit 0
