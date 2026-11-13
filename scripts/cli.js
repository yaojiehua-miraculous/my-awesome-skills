#!/usr/bin/env node
/**
 * my-awesome-skills 安装器（零依赖，Node 18+）
 *
 * 用法：
 *   npx my-awesome-skills                 装到默认宿主目录
 *   npx my-awesome-skills --host agents   指定宿主（dsh / agents / claude / codex / cursor）
 *   npx my-awesome-skills --dest <路径>   装到任意目录
 *   npx my-awesome-skills --all           装到所有检测到的宿主
 *   npx my-awesome-skills --link          用符号链接代替复制
 *   npx my-awesome-skills --unlink        卸载
 *   npx my-awesome-skills --list          查看当前装了什么
 *   npx my-awesome-skills --dry-run       只打印计划
 */

const fs = require("fs");
const os = require("os");
const path = require("path");

const PKG_ROOT = path.resolve(__dirname, "..");
const HOME = os.homedir();
const SOURCE_ROOTS = ["skills", "personal"];

const HOSTS = {
  dsh: path.join(HOME, ".dsh", "skills"),
  agents: path.join(HOME, ".agents", "skills"),
  claude: path.join(HOME, ".claude", "skills"),
  codex: path.join(HOME, ".codex", "skills"),
  cursor: path.join(HOME, ".cursor", "skills"),
};

const args = process.argv.slice(2);
const has = (flag) => args.includes(flag);
const valueOf = (flag) => {
  const i = args.indexOf(flag);
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : null;
};

if (has("--help") || has("-h")) {
  console.log(fs.readFileSync(__filename, "utf8").split("*/")[0].replace(/^#!.*\n\/\*\*/, "").replace(/^ \* ?/gm, ""));
  process.exit(0);
}

const DRY = has("--dry-run");
const UNLINK = has("--unlink");
const LIST = has("--list");
const LINK = has("--link");
const DEST = valueOf("--dest");
const HOST = valueOf("--host");

function collectSkills() {
  const out = [];
  for (const rootName of SOURCE_ROOTS) {
    const root = path.join(PKG_ROOT, rootName);
    if (!fs.existsSync(root)) continue;
    for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const dir = path.join(root, entry.name);
      if (!fs.existsSync(path.join(dir, "SKILL.md"))) continue;
      out.push({ name: entry.name, dir });
    }
  }
  return out.sort((a, b) => a.name.localeCompare(b.name));
}

function resolveTargets(skills) {
  if (DEST) return [path.resolve(DEST.replace(/^~(?=$|\/|\\)/, HOME))];
  if (HOST) {
    if (!HOSTS[HOST]) {
      console.error(`未知宿主: ${HOST}（可选: ${Object.keys(HOSTS).join(" / ")}）`);
      process.exit(1);
    }
    return [HOSTS[HOST]];
  }
  if (has("--all")) return Object.values(HOSTS);
  // 默认跟着你已在用的宿主走，避免同一批技能在多个扫描根里重复
  if (fs.existsSync(path.join(HOME, ".dsh"))) return [HOSTS.dsh];
  return [HOSTS.agents];
}

function skillNameOf(dir) {
  try {
    const text = fs.readFileSync(path.join(dir, "SKILL.md"), "utf8").replace(/^\uFEFF/, "");
    const m = text.match(/^---[\s\S]*?\nname:\s*(.+)$/m);
    return m ? m[1].trim() : null;
  } catch {
    return null;
  }
}

function isInside(parent, child) {
  const rel = path.relative(path.resolve(parent), path.resolve(child));
  return rel && !rel.startsWith("..") && !path.isAbsolute(rel);
}

function installOne(skill, target) {
  const dest = path.join(target, skill.name);
  if (fs.existsSync(dest)) {
    console.log(`  跳过 ${skill.name}（已存在）`);
    return "skip";
  }
  if (DRY) {
    console.log(`  [would] ${skill.name} → ${dest}`);
    return "add";
  }
  fs.mkdirSync(target, { recursive: true });
  try {
    if (LINK) {
      fs.symlinkSync(skill.dir, dest, process.platform === "win32" ? "junction" : "dir");
    } else {
      fs.cpSync(skill.dir, dest, { recursive: true });
    }
  } catch (err) {
    console.log(`  失败 ${skill.name}: ${err.message}`);
    return "fail";
  }
  console.log(`  安装 ${skill.name}`);
  return "add";
}

function uninstallOne(skill, target) {
  const dest = path.join(target, skill.name);
  if (!fs.existsSync(dest)) return "skip";
  if (!isInside(target, dest)) {
    console.log(`  跳过 ${skill.name}（路径越界，不动它）`);
    return "skip";
  }
  const name = skillNameOf(dest);
  if (name !== skill.name) {
    console.log(`  跳过 ${skill.name}（同名但内容不是我们的技能）`);
    return "skip";
  }
  if (DRY) {
    console.log(`  [would] 移除 ${dest}`);
    return "removed";
  }
  fs.rmSync(dest, { recursive: true, force: true });
  console.log(`  移除 ${skill.name}`);
  return "removed";
}

function main() {
  const skills = collectSkills();
  if (!skills.length) {
    console.error("包里没有找到任何技能（skills/*/SKILL.md）。");
    process.exit(1);
  }
  const targets = resolveTargets(skills);

  if (LIST) {
    for (const target of targets) {
      console.log(`\n${target}`);
      for (const skill of skills) {
        const dest = path.join(target, skill.name);
        console.log(`  ${fs.existsSync(dest) ? "已装" : "未装"}  ${skill.name}`);
      }
    }
    return;
  }

  console.log(`my-awesome-skills · ${skills.length} 个技能${DRY ? "（dry-run）" : ""}`);
  for (const target of targets) {
    console.log(`\n目标: ${target}`);
    let add = 0, skip = 0, fail = 0, removed = 0;
    for (const skill of skills) {
      const result = UNLINK ? uninstallOne(skill, target) : installOne(skill, target);
      if (result === "add") add++;
      else if (result === "removed") removed++;
      else if (result === "fail") fail++;
      else skip++;
    }
    const label = UNLINK ? `移除 ${removed}` : `新装 ${add}`;
    console.log(`  → ${label} · 跳过 ${skip} · 失败 ${fail}`);
    if (fail) process.exitCode = 1;
  }

  if (!UNLINK && !DRY) {
    console.log("\n下一步：");
    console.log("  1) 打开 AI 编码工具的新会话");
    console.log("  2) 问一句模糊的真实问题，看第一段是不是【路由】结论");
    console.log("  3) 撤销：npx my-awesome-skills --unlink");
  }
}

main();
