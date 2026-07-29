from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional

SKILLCTL_DIR = Path.home() / ".skillctl"
INDEX_DIR = SKILLCTL_DIR / "index"
INSTALLED_PATH = SKILLCTL_DIR / "installed.json"
CONFIG_PATH = SKILLCTL_DIR / "config.json"
AUDIT_DIR = SKILLCTL_DIR / "audit"
CACHE_DIR = SKILLCTL_DIR / "cache"

DEFAULT_CONFIG = {
    "index_repo": "https://github.com/agent-skills/index.git",
    "auto_update_index": True,
    "language": "auto",
    "llm_provider": None,
    "llm_config": {},
}

def ensure_dirs() -> None:
    """如果不存在则创建 ~/.skillctl/ 及其子目录"""
    SKILLCTL_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    """加载用户配置，不存在时创建默认配置"""
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    return json.loads(CONFIG_PATH.read_text())

def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))

def load_installed() -> list[dict]:
    """加载已安装技能清单"""
    if not INSTALLED_PATH.exists():
        return []
    return json.loads(INSTALLED_PATH.read_text())

def save_installed(entries: list[dict]) -> None:
    INSTALLED_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

def record_installation(name: str, version: str, repo: str, platform: str) -> None:
    """记录一次安装到 ~/.skillctl/installed.json"""
    entries = load_installed()
    # 覆盖同名技能的旧记录
    entries = [e for e in entries if e["name"] != name]
    entries.append({
        "name": name,
        "version": version,
        "repo": repo,
        "platform": platform,
        "installed_at": __import__("datetime").datetime.now().isoformat(),
    })
    save_installed(entries)
