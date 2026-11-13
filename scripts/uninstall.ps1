# 撤销挂载：只删除 ~/.dsh/skills 下的联接，仓库里的技能文件不受影响
# 由 uninstall.cmd 双击调用

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $env:USERPROFILE '.dsh\skills'

Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  my-awesome-skills 卸载挂载' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host "  只删除 $dest 下的联接，仓库文件不受影响。"
Write-Host '================================================'
Write-Host ''

if (-not (Test-Path $dest)) {
    Write-Host '目标目录不存在，本来就没装。'
    exit 0
}

$removed = 0; $skip = 0

foreach ($rootName in @('skills', 'personal')) {
    $root = Join-Path $repo $rootName
    if (-not (Test-Path $root)) { continue }

    Get-ChildItem -Path $root -Directory | Sort-Object Name | ForEach-Object {
        $name = $_.Name
        $target = Join-Path $dest $name

        if (-not (Test-Path $target)) {
            $script:skip++
            return
        }

        $item = Get-Item $target -Force -ErrorAction SilentlyContinue
        $isLink = $item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)

        if (-not $isLink) {
            Write-Host "  跳过 $name（不是联接，可能被替换成了真实目录）" -ForegroundColor DarkGray
            $script:skip++
            return
        }

        try {
            # 目录联接必须用 rmdir 删，Remove-Item 会误删源目录内容
            [System.IO.Directory]::Delete($target, $false)
            Write-Host "  移除 $name" -ForegroundColor Green
            $script:removed++
        }
        catch {
            Write-Host "  跳过 $name（正被占用？关掉编辑器再试）" -ForegroundColor Yellow
            $script:skip++
        }
    }
}

Write-Host ''
Write-Host '------------------------------------------------'
Write-Host "  已移除 $removed 个 · 跳过 $skip 个"
Write-Host '------------------------------------------------'
exit 0
