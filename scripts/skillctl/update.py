from __future__ import annotations
import argparse
import subprocess

from scripts.skillctl.config import load_installed, save_installed, CACHE_DIR
from scripts.skillctl.index import load_registry
from scripts.skillctl.models import SkillEntry

def cmd_update(args: argparse.Namespace) -> int:
    installed = load_installed()
    if not installed:
        print("  没有已安装的技能。")
        return 0

    registry = load_registry()

    if args.name:
        installed = [s for s in installed if s["name"] == args.name]
        if not installed:
            print(f"  '{args.name}' 并未安装。")
            return 1

    updated_any = False
    for skill in installed:
        name = skill["name"]
        current_version = skill["version"]

        entry = registry.skills.get(name)
        if not entry:
            print(f"  {name}：在注册表中未找到（可能已被移除）")
            continue

        if entry.version == current_version:
            print(f"  {name}：已是最新（v{current_version}）")
            continue

        print(f"  {name}：v{current_version} → v{entry.version}")
        if not args.check:
            _perform_upgrade(name, entry)
            skill["version"] = entry.version
            updated_any = True

    if updated_any:
        save_installed(installed)
        print("\n  ✓ 更新完成。")
    return 0

def _perform_upgrade(name: str, entry: SkillEntry) -> bool:
    cache_path = CACHE_DIR / name
    if not cache_path.exists():
        print(f"  {name}：缓存未找到，建议重新安装")
        return False

    result = subprocess.run(
        ["git", "-C", str(cache_path), "fetch", "--tags"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  {name}：fetch 失败：{result.stderr.strip()}")
        return False

    result = subprocess.run(
        ["git", "-C", str(cache_path), "checkout", f"v{entry.version}"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  {name}：已签出 v{entry.version}")
        return True
    print(f"  {name}：签出失败")
    return False
