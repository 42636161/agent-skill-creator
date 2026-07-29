from __future__ import annotations
import json
import subprocess
from pathlib import Path

from scripts.skillctl.config import INDEX_DIR, load_config
from scripts.skillctl.models import Registry, SkillEntry, Category, Author, SemanticMetadata

def ensure_index() -> Path:
    """克隆或拉取索引仓库。返回仓库根目录路径"""
    config = load_config()
    repo_url = config.get("index_repo", "https://github.com/agent-skills/index.git")

    if not INDEX_DIR.exists():
        return _clone_index(repo_url)

    if config.get("auto_update_index", True):
        _pull_index()

    return INDEX_DIR

def _clone_index(repo_url: str) -> Path:
    subprocess.run(
        ["git", "clone", "--depth=1", repo_url, str(INDEX_DIR)],
        capture_output=True, check=True
    )
    return INDEX_DIR

def _pull_index() -> None:
    subprocess.run(
        ["git", "-C", str(INDEX_DIR), "pull", "--ff-only"],
        capture_output=True
    )

def load_registry() -> Registry:
    """从索引仓库解析 registry.json 为 Registry 数据类"""
    ensure_index()
    reg_path = INDEX_DIR / "registry.json"
    if not reg_path.exists():
        raise FileNotFoundError(f"registry.json 在索引仓库中未找到：{reg_path}")

    data = json.loads(reg_path.read_text())
    skills: dict[str, SkillEntry] = {}
    for s in data.get("skills", []):
        author = Author(
            name=s.get("author", {}).get("name", "unknown"),
            url=s.get("author", {}).get("url", ""),
        )
        semantic = None
        if "semantic" in s:
            sem = s["semantic"]
            semantic = SemanticMetadata(
                intents=sem.get("intents", []),
                prompt_triggers=sem.get("prompt_triggers", []),
                requires=sem.get("requires", []),
                produces=sem.get("produces", []),
            )
        entry = SkillEntry(
            name=s["name"],
            display_name=s.get("display_name", s["name"]),
            version=s.get("version", "0.0.0"),
            description=s.get("description", ""),
            repo=s.get("repo", ""),
            author=author,
            tags=s.get("tags", []),
            category=s.get("category", ""),
            platforms=s.get("platforms", []),
            license=s.get("license", ""),
            created=s.get("created", ""),
            updated=s.get("updated", ""),
            verified=s.get("verified", False),
            min_cli_version=s.get("min_cli_version", ""),
            semantic=semantic,
            dependencies=s.get("dependencies", []),
            install_count=s.get("install_count", 0),
        )
        skills[s["name"]] = entry

    categories: dict[str, Category] = {}
    for c in data.get("categories", []):
        categories[c["id"]] = Category(
            id=c["id"],
            name=c.get("name", c["id"]),
            description=c.get("description", ""),
        )

    reg = data.get("registry", {})
    return Registry(
        skills=skills,
        categories=categories,
        schema_version=reg.get("schema_version", "2"),
        github_org=reg.get("github_org", "agent-skills"),
        updated=reg.get("updated", ""),
    )

def search_registry(registry: Registry, query: str) -> list[SkillEntry]:
    """按技能名称、展示名、描述、标签进行关键词搜索"""
    q = query.lower()
    results = []
    for entry in registry.skills.values():
        if (q in entry.name.lower()
                or q in entry.display_name.lower()
                or q in entry.description.lower()
                or any(q in t.lower() for t in entry.tags)):
            results.append(entry)
    return results
