from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def cmd_publish(args: argparse.Namespace) -> int:
    """将技能发布到 GitHub 并注册到索引仓库"""
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    org = args.org or "agent-skills"

    if not skill_dir.exists():
        print(f"错误：技能目录不存在：{skill_dir}")
        return 1

    print(f"\n  预检：{skill_dir}\n")

    # Add repo scripts dir to path for validate/security_scan imports
    repo_scripts = Path(__file__).resolve().parent.parent
    if str(repo_scripts) not in sys.path:
        sys.path.insert(0, str(repo_scripts))

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print("  ✗ SKILL.md 未找到 — 中止")
        return 1

    content = skill_md.read_text()
    frontmatter = _parse_frontmatter(content)
    skill_name = frontmatter.get("name", skill_dir.name)
    version = frontmatter.get("metadata", {}).get("version", "1.0.0")
    author_name = frontmatter.get("metadata", {}).get("author", "unknown")
    description = frontmatter.get("description", "")

    print(f"  名称：      {skill_name}")
    print(f"  版本：      {version}")
    print(f"  作者：      {author_name}")
    print(f"  描述：      {description[:60]}...")
    print()

    if args.dry_run:
        print("  [DRY RUN] 预检完成。去掉 --dry-run 即可正式发布。")
        return 0

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("  ✗ GITHUB_TOKEN 或 GH_TOKEN 未设置")
        return 1

    repo_name = skill_name
    repo_full = f"{org}/{repo_name}"
    print(f"  创建仓库：{repo_full}")

    result = subprocess.run(
        ["gh", "repo", "view", repo_full, "--json", "name"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["gh", "repo", "create", repo_full, "--public", "--description", description[:100]],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  ✗ 创建仓库失败：{result.stderr.strip()}")
            return 1
        print("  ✓ 仓库已创建")
    else:
        print("  ✓ 仓库已存在")

    print("  推送技能内容...")
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        repo_tmp = tmp_dir / skill_name
        shutil.copytree(skill_dir, repo_tmp, ignore=_ignore_patterns())
        subprocess.run(["git", "init"], capture_output=True, cwd=str(repo_tmp))
        subprocess.run(["git", "add", "-A"], capture_output=True, cwd=str(repo_tmp))
        subprocess.run(
            ["git", "commit", "-m", f"chore: 初始提交 v{version}"],
            capture_output=True, cwd=str(repo_tmp),
        )
        subprocess.run(
            ["git", "remote", "add", "origin", f"https://github.com/{repo_full}.git"],
            capture_output=True, cwd=str(repo_tmp),
        )
        result = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            capture_output=True, text=True, cwd=str(repo_tmp),
        )
        if result.returncode != 0:
            print(f"  ✗ 推送失败：{result.stderr.strip()}")
            return 1
        subprocess.run(["git", "tag", f"v{version}"], capture_output=True, cwd=str(repo_tmp))
        subprocess.run(["git", "push", "origin", f"v{version}"], capture_output=True, cwd=str(repo_tmp))
        print("  ✓ 内容已推送（带 tag v{version}）")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("  注册到索引...")
    _register_in_index(skill_name, repo_full, version, description, author_name, org)

    print(f"\n  ✓ 已发布：https://github.com/{repo_full}")
    print(f"  试试：python3 scripts/skillctl/__main__.py install {skill_name}")
    return 0

def _parse_frontmatter(content: str) -> dict:
    """解析 --- 标记之间的 frontmatter，支持 YAML 多行值和嵌套 metadata"""
    lines = content.split("\n")
    if not lines or not lines[0].strip() == "---":
        return {}

    result = {}
    metadata = {}
    in_metadata = False
    in_multiline = None

    for line in lines[1:]:
        raw = line
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped == "metadata:":
            in_metadata = True
            continue
        if in_metadata and raw.startswith("  ") and not raw.strip().startswith("-"):
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                metadata[k.strip()] = v.strip().strip('"').strip("'")
            continue
        in_metadata = False
        if in_multiline and stripped:
            result[in_multiline] = (result.get(in_multiline, "") + " " + stripped).strip()
            in_multiline = None
            continue
        if stripped and not raw.startswith(" ") and ":" in stripped:
            k, v = stripped.split(":", 1)
            v = v.strip()
            if v == ">-" or v == "|":
                in_multiline = k
                continue
            result[k.strip()] = v.strip().strip('"').strip("'")

    if metadata:
        result["metadata"] = metadata
    return result

def _register_in_index(skill_name: str, repo_full: str, version: str,
                        description: str, author_name: str, org: str) -> None:
    """将技能条目添加到本地索引克隆并提交推送"""
    from scripts.skillctl.index import ensure_index
    from scripts.skillctl.config import INDEX_DIR
    import datetime

    ensure_index()

    entry = {
        "name": skill_name,
        "display_name": skill_name.replace("-", " ").title(),
        "version": version,
        "description": description,
        "repo": f"https://github.com/{repo_full}",
        "author": {"name": author_name, "url": f"https://github.com/{author_name}"},
        "tags": [skill_name],
        "verified": True,
        "created": datetime.date.today().isoformat(),
        "updated": datetime.date.today().isoformat(),
    }

    reg_path = INDEX_DIR / "registry.json"
    data = json.loads(reg_path.read_text()) if reg_path.exists() else {"skills": []}

    existing = [s for s in data.get("skills", []) if s["name"] != skill_name]
    existing.append(entry)
    data["skills"] = existing
    data.setdefault("registry", {})["updated"] = datetime.datetime.now().isoformat()

    reg_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    subprocess.run(["git", "-C", str(INDEX_DIR), "add", "registry.json"], capture_output=True)
    result = subprocess.run(
        ["git", "-C", str(INDEX_DIR), "commit", "-m", f"feat: 注册 {skill_name} v{version}"],
        capture_output=True, text=True,
    )
    if "nothing to commit" not in result.stdout:
        subprocess.run(["git", "-C", str(INDEX_DIR), "push"], capture_output=True)

def _ignore_patterns():
    import shutil
    return shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv", "venv", ".DS_Store")
