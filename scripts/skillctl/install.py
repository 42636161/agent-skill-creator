from __future__ import annotations
import argparse
import subprocess
import sys
import shutil
from pathlib import Path

from scripts.skillctl.index import load_registry
from scripts.skillctl.config import record_installation, CACHE_DIR, ensure_dirs
from scripts.skillctl.models import SkillEntry
from scripts.platforms import user_paths

def resolve_skill_entry(name: str) -> SkillEntry | None:
    """在注册表中按精确名称查找技能"""
    registry = load_registry()
    return registry.skills.get(name)

def resolve_install_dir(platform: str | None, custom_dir: str | None) -> Path:
    """确定安装目标目录"""
    if custom_dir:
        return Path(custom_dir).expanduser().resolve()
    if not platform:
        platform = _detect_current_platform()
    paths = user_paths()
    target = paths.get(platform)
    if not target:
        print(f"未知平台：{platform}")
        print(f"支持：{', '.join(paths.keys())}")
        sys.exit(1)
    return Path(target).expanduser().resolve()

def _detect_current_platform() -> str:
    """自动检测当前 Agent 平台"""
    home = Path.home()
    markers = {
        "claude-code": home / ".claude",
        "cursor": home / ".cursor",
        "windsurf": home / ".codeium" / "windsurf",
        "codex": home / ".agents",
        "gemini": home / ".gemini",
        "cline": home / ".cline",
    }
    for platform, marker in markers.items():
        if marker.exists():
            return platform
    return "universal"

def install_from_git(repo_url: str, version: str, target_dir: Path, skill_name: str) -> bool:
    """从 Git 仓库克隆技能并调用安装脚本"""
    ensure_dirs()
    cache_path = CACHE_DIR / skill_name
    if cache_path.exists():
        shutil.rmtree(cache_path)

    print(f"  正在克隆 {repo_url}...")
    result = subprocess.run(
        ["git", "clone", "--depth=1", "--branch", f"v{version}", repo_url, str(cache_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  分支 v{version} 未找到，克隆默认分支...")
        result = subprocess.run(
            ["git", "clone", "--depth=1", repo_url, str(cache_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  克隆失败：{result.stderr.strip()}")
            return False

    install_sh = cache_path / "scripts" / "install-skill.sh"
    if not install_sh.exists():
        install_sh = cache_path / "install.sh"
    if not install_sh.exists():
        return _copy_skill_directly(cache_path, target_dir, skill_name)

    print(f"  执行安装：{install_sh}")
    result = subprocess.run(
        ["bash", str(install_sh), str(cache_path), "--target", str(target_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  安装失败：{result.stderr.strip()}")
        return False
    print(result.stdout)
    return True

def _copy_skill_directly(src: Path, target_dir: Path, skill_name: str) -> bool:
    """回退方案：直接复制技能目录"""
    target = target_dir / skill_name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target)
    return True

def cmd_doctor(args: argparse.Namespace) -> int:
    """检查 CLI 和索引仓库健康状态"""
    from scripts.skillctl.config import SKILLCTL_DIR
    from scripts.skillctl.index import ensure_index, load_registry as lr

    print("\n  skillctl 健康检查\n")
    print(f"  状态目录：     {SKILLCTL_DIR}")
    print(f"  状态存在：     {'✓' if SKILLCTL_DIR.exists() else '✗ 未初始化'}")
    try:
        ensure_index()
        print("  索引仓库：     ✓ 已克隆/可访问")
    except Exception as e:
        print(f"  索引仓库：     ✗ {e}")
        return 1
    try:
        reg = lr()
        print(f"  注册表：       ✓ {len(reg.skills)} 个技能，{len(reg.categories)} 个分类")
    except Exception as e:
        print(f"  注册表：       ✗ {e}")
        return 1
    print()
    return 0

def cmd_install(args: argparse.Namespace) -> int:
    """安装技能：支持精确名称和自然语言查询"""
    skill_name = args.target.split("@")[0]
    version = args.target.split("@")[1] if "@" in args.target else None

    entry = resolve_skill_entry(skill_name)
    if not entry:
        from scripts.skillctl.search import semantic_search
        registry = load_registry()
        results = semantic_search(registry, args.target, top_k=1)
        if results:
            entry = results[0]
            print(f"  将「{args.target}」理解为：{entry.display_name}")
        else:
            print(f"  技能「{skill_name}」未找到。试试 'python3 scripts/skillctl/__main__.py search {skill_name}'")
            return 1

    target_version = version or entry.version
    install_dir = resolve_install_dir(args.platform, args.dir)

    print(f"\n  正在安装 {entry.display_name} v{target_version}")
    print(f"  目标位置：   {install_dir}")
    print(f"  认证状态：   {'✓ 已认证' if entry.verified else '⚠ 第三方技能'}")
    print()

    if not entry.verified:
        response = input("  此技能来自第三方发布者。继续安装？(y/N)：")
        if response.lower() != "y":
            print("  安装已取消。")
            return 1

    install_dir.mkdir(parents=True, exist_ok=True)
    success = install_from_git(entry.repo, target_version, install_dir, entry.name)
    if success:
        record_installation(entry.name, target_version, entry.repo, args.platform or "auto")
        print(f"\n  ✓ {entry.display_name} v{target_version} 已安装到 {install_dir}")
        print(f"  执行 'python3 scripts/skillctl/__main__.py update {entry.name}' 检查更新。")
    else:
        print(f"\n  ✗ {entry.display_name} 安装失败")
        return 1
    return 0
