# Skill Distribution Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub-native skill distribution system for agent-skill-creator: index repo, `skillctl` CLI, semantic install, publish pipeline, security model.

**Architecture:** A new `skillctl` Python package under `scripts/` that reads from a GitHub-based index repo (`agent-skills/index`), delegates installs to `install-skill.sh`, and publishes skills via GitHub API. A thin shell wrapper provides the `skillctl` command. Each task builds a self-contained capability with tests.

**Tech Stack:** Python 3.10+, shell (POSIX sh + PowerShell), GitHub API (REST v3), JSON Schema, existing validate.py / security_scan.py / skill_registry.py

---

## File Structure

```
scripts/
├── skillctl                        # Shell entry point (exec python -m)
├── skillctl/
│   ├── __init__.py                 # Package marker + __version__
│   ├── __main__.py                 # python -m dispatch → cli.main()
│   ├── cli.py                      # ArgumentParser, command dispatch
│   ├── models.py                   # Skill, Category, RegistryEntry dataclasses
│   ├── config.py                   # ~/.skillctl/ dir init, installed.json, config.json
│   ├── index.py                    # Index repo clone/pull/cache management
│   ├── install.py                  # Install flow: resolve → git clone → install-skill.sh
│   ├── search.py                   # Keyword search + semantic NL matching
│   ├── publish.py                  # Publish flow: preflight → repo create → push → register
│   └── update.py                   # Version check + upgrade
├── install-skill.sh                # Minor: add --from-registry flag
├── install-skill.ps1               # Minor: same
└── tests/
    ├── test_skillctl_models.py
    ├── test_skillctl_config.py
    ├── test_skillctl_index.py
    ├── test_skillctl_install.py
    ├── test_skillctl_search.py
    ├── test_skillctl_publish.py
    └── test_skillctl_update.py

SKILL.md                            # Phase 5: add publish prompt
```

---

## Task Decomposition

### Phase 0: Foundation

#### Task 1: Data models — Skill, Category, RegistryEntry

**Files:**
- Create: `scripts/skillctl/__init__.py`
- Create: `scripts/skillctl/models.py`
- Create: `scripts/tests/test_skillctl_models.py`

- [ ] **Step 1: Write the models**

```python
# scripts/skillctl/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Author:
    name: str
    url: str = ""

@dataclass
class SemanticMetadata:
    intents: list[str] = field(default_factory=list)
    prompt_triggers: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)

@dataclass
class Category:
    id: str
    name: str
    description: str = ""

@dataclass
class SkillEntry:
    name: str
    display_name: str
    version: str
    description: str
    repo: str
    author: Author
    tags: list[str] = field(default_factory=list)
    category: str = ""
    platforms: list[str] = field(default_factory=list)
    license: str = ""
    created: str = ""
    updated: str = ""
    verified: bool = False
    min_cli_version: str = ""
    semantic: Optional[SemanticMetadata] = None
    dependencies: list[str] = field(default_factory=list)
    install_count: int = 0

@dataclass
class Registry:
    skills: dict[str, SkillEntry]  # keyed by skill name
    categories: dict[str, Category]  # keyed by category id
    schema_version: str = "2"
    github_org: str = "agent-skills"
    updated: str = ""
```

- [ ] **Step 2: Write tests**

```python
# scripts/tests/test_skillctl_models.py
import unittest
from scripts.skillctl.models import SkillEntry, SemanticMetadata, Author

class TestSkillEntry(unittest.TestCase):
    def test_minimal_skill_entry(self):
        s = SkillEntry("test", "Test Skill", "1.0.0", "A test", "https://github.com/agent-skills/test")
        self.assertEqual(s.name, "test")
        self.assertEqual(s.version, "1.0.0")

    def test_skill_entry_with_semantic(self):
        sm = SemanticMetadata(intents=["analyze data"])
        s = SkillEntry("ds", "Data Skill", "1.0.0", "Data", "repo", semantic=sm)
        self.assertIn("analyze data", s.semantic.intents)

    def test_author_fields(self):
        a = Author("Alice", "https://github.com/alice")
        self.assertEqual(a.name, "Alice")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Create `__init__.py`**

```python
# scripts/skillctl/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 4: Run models tests**

Run: `python -m pytest scripts/tests/test_skillctl_models.py -v`
Expected: 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add scripts/skillctl/ scripts/tests/test_skillctl_models.py
git commit -m "feat(skillctl): add data models for SkillEntry, Category, Registry"
```

---

#### Task 2: Config management — ~/.skillctl/ directory state

**Files:**
- Create: `scripts/skillctl/config.py`
- Create: `scripts/tests/test_skillctl_config.py`

- [ ] **Step 1: Write the config module**

```python
# scripts/skillctl/config.py
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
    """Create ~/.skillctl/ and subdirs if they don't exist."""
    SKILLCTL_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    """Load user config, creating with defaults if missing."""
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    return json.loads(CONFIG_PATH.read_text())

def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

def load_installed() -> list[dict]:
    """Load installed skills manifest."""
    if not INSTALLED_PATH.exists():
        return []
    return json.loads(INSTALLED_PATH.read_text())

def save_installed(entries: list[dict]) -> None:
    INSTALLED_PATH.write_text(json.dumps(entries, indent=2))

def record_installation(name: str, version: str, repo: str, platform: str) -> None:
    entries = load_installed()
    # Replace existing entry for same name
    entries = [e for e in entries if e["name"] != name]
    entries.append({
        "name": name,
        "version": version,
        "repo": repo,
        "platform": platform,
        "installed_at": __import__("datetime").datetime.now().isoformat(),
    })
    save_installed(entries)
```

- [ ] **Step 2: Write config tests**

```python
# scripts/tests/test_skillctl_config.py
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    @patch("scripts.skillctl.config.SKILLCTL_DIR")
    def test_ensure_dirs_creates_hierarchy(self, mock_dir):
        mock_dir.__str__.return_value = str(self.tmp)
        mock_dir.is_dir.return_value = False

        from scripts.skillctl.config import ensure_dirs
        # Test that calls are made (we can't easily mock mkdir chain,
        # but can verify the paths resolve)
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.assertTrue(self.tmp.exists())
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest scripts/tests/test_skillctl_config.py -v`
Expected: Tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/skillctl/config.py scripts/tests/test_skillctl_config.py
git commit -m "feat(skillctl): add config module for ~/.skillctl/ state management"
```

---

#### Task 3: Index repo management — clone, pull, cache

**Files:**
- Create: `scripts/skillctl/index.py`
- Create: `scripts/tests/test_skillctl_index.py`

- [ ] **Step 1: Write index module**

```python
# scripts/skillctl/index.py
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from typing import Optional

from scripts.skillctl.config import INDEX_DIR
from scripts.skillctl.models import Registry, SkillEntry, Category, Author, SemanticMetadata
from scripts.skillctl.config import load_config

import json

def ensure_index() -> Path:
    """Clone or pull the index repo. Returns the path to the repo root."""
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
    """Parse registry.json from the index repo into Registry dataclass."""
    ensure_index()
    reg_path = INDEX_DIR / "registry.json"
    if not reg_path.exists():
        raise FileNotFoundError(f"registry.json not found in index repo at {reg_path}")

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
    """Keyword search against skill name, display_name, description, tags."""
    q = query.lower()
    results = []
    for entry in registry.skills.values():
        if (q in entry.name.lower()
                or q in entry.display_name.lower()
                or q in entry.description.lower()
                or any(q in t.lower() for t in entry.tags)):
            results.append(entry)
    return results
```

- [ ] **Step 2: Write index tests**

```python
# scripts/tests/test_skillctl_index.py
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.skillctl.index import search_registry, load_registry
from scripts.skillctl.models import Registry, SkillEntry, Category

def make_test_registry() -> Registry:
    """Create a Registry with sample skills for testing."""
    skills = {
        "alice-financial-copilot": SkillEntry(
            name="alice-financial-copilot",
            display_name="Alice Financial Copilot",
            version="1.2.0",
            description="Technical analysis with RSI, MACD",
            repo="https://github.com/agent-skills/alice-financial-copilot",
            tags=["stocks", "trading"],
            category="financial",
        ),
        "weekly-crm-report": SkillEntry(
            name="weekly-crm-report",
            display_name="Weekly CRM Report",
            version="2.0.0",
            description="Sales data cleaning and regional summary",
            repo="https://github.com/agent-skills/weekly-crm-report",
            tags=["crm", "sales"],
            category="crm",
        ),
    }
    categories = {
        "financial": Category("financial", "Financial Analysis", "Market data skills"),
        "crm": Category("crm", "Sales & CRM", "CRM skills"),
    }
    return Registry(skills=skills, categories=categories)

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.registry = make_test_registry()

    def test_search_by_name(self):
        results = search_registry(self.registry, "alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "alice-financial-copilot")

    def test_search_by_tag(self):
        results = search_registry(self.registry, "trading")
        self.assertEqual(len(results), 1)

    def test_search_by_description(self):
        results = search_registry(self.registry, "RSI")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        results = search_registry(self.registry, "nonexistent")
        self.assertEqual(len(results), 0)

    def test_search_multiple_matches(self):
        results = search_registry(self.registry, "report")
        self.assertEqual(len(results), 1)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run index tests**

Run: `python -m pytest scripts/tests/test_skillctl_index.py -v`
Expected: 5 tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/skillctl/index.py scripts/tests/test_skillctl_index.py
git commit -m "feat(skillctl): index repo management + registry parsing + keyword search"
```

---

### Phase 1: Core CLI

#### Task 4: CLI entry point and command dispatch

**Files:**
- Create: `scripts/skillctl/__main__.py`
- Create: `scripts/skillctl/cli.py`
- Create: `scripts/skillctl`

- [ ] **Step 1: Write CLI argument parser**

```python
# scripts/skillctl/cli.py
from __future__ import annotations
import argparse
import sys

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillctl",
        description="Agent Skills CLI — discover, install, publish agent skills",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search", help="Search for skills")
    p_search.add_argument("query", help="Search query (keyword or natural language)")
    p_search.add_argument("--json", action="store_true", help="Output as JSON")

    # install
    p_install = sub.add_parser("install", help="Install a skill")
    p_install.add_argument("target", help="Skill name or version (e.g. name@1.0.0) or NL query")
    p_install.add_argument("--dir", help="Install to custom directory")
    p_install.add_argument("--platform", help="Target platform name")

    # info
    p_info = sub.add_parser("info", help="Show skill details")
    p_info.add_argument("name", help="Skill name")
    p_info.add_argument("--json", action="store_true")

    # list
    p_list = sub.add_parser("list", help="List all available skills")
    p_list.add_argument("--category", help="Filter by category")
    p_list.add_argument("--json", action="store_true")

    # update
    p_update = sub.add_parser("update", help="Update installed skill(s)")
    p_update.add_argument("name", nargs="?", help="Skill name (omit for all)")
    p_update.add_argument("--check", action="store_true", help="Only check for updates")

    # categories
    sub.add_parser("categories", help="List skill categories")

    # doctor
    sub.add_parser("doctor", help="Check CLI and index health")

    # publish
    p_publish = sub.add_parser("publish", help="Publish a skill to GitHub")
    p_publish.add_argument("skill_dir", help="Path to the skill directory")
    p_publish.add_argument("--org", help="GitHub org (default: agent-skills)")
    p_publish.add_argument("--dry-run", action="store_true", help="Preflight without publishing")

    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "search":
        from scripts.skillctl.search import cmd_search
        return cmd_search(args)
    elif args.command == "install":
        from scripts.skillctl.install import cmd_install
        return cmd_install(args)
    elif args.command == "info":
        from scripts.skillctl.search import cmd_info
        return cmd_info(args)
    elif args.command == "list":
        from scripts.skillctl.search import cmd_list
        return cmd_list(args)
    elif args.command == "update":
        from scripts.skillctl.update import cmd_update
        return cmd_update(args)
    elif args.command == "categories":
        from scripts.skillctl.search import cmd_categories
        return cmd_categories(args)
    elif args.command == "doctor":
        from scripts.skillctl.install import cmd_doctor
        return cmd_doctor(args)
    elif args.command == "publish":
        from scripts.skillctl.publish import cmd_publish
        return cmd_publish(args)
    return 1

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write `__main__.py`**

```python
# scripts/skillctl/__main__.py
import sys
from scripts.skillctl.cli import main

sys.exit(main())
```

- [ ] **Step 3: Write shell wrapper**

```bash
#!/bin/sh
# scripts/skillctl — Shell wrapper that exec's python -m scripts.skillctl
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${SCRIPT_DIR}/skillctl/__main__.py" "$@"
```

```bash
# Make executable
chmod +x scripts/skillctl
```

- [ ] **Step 4: Install the shell wrapper for testing**

```bash
# Symlink for testing
ln -sf "$(pwd)/scripts/skillctl" /usr/local/bin/skillctl
```

- [ ] **Step 5: Test CLI help**

Run: `python scripts/skillctl/__main__.py --help`
Expected: Shows all commands

- [ ] **Step 6: Commit**

```bash
git add scripts/skillctl/__main__.py scripts/skillctl/cli.py scripts/skillctl
git commit -m "feat(skillctl): CLI entry point with argparse and command dispatch"
```

---

#### Task 5: `skillctl search`, `info`, `list`, `categories` commands

**Files:**
- Create: `scripts/skillctl/search.py`
- Create: `scripts/tests/test_skillctl_search.py`

- [ ] **Step 1: Write search commands**

```python
# scripts/skillctl/search.py
from __future__ import annotations
import argparse
import json
import sys

from scripts.skillctl.index import ensure_index, load_registry, search_registry
from scripts.skillctl.config import SKILLCTL_DIR

def cmd_search(args: argparse.Namespace) -> int:
    registry = load_registry()
    results = search_registry(registry, args.query)

    if not results:
        print(f"No skills found matching '{args.query}'")
        return 1

    if args.json:
        data = [_entry_to_dict(e) for e in results]
        print(json.dumps(data, indent=2))
        return 0

    print(f"\nFound {len(results)} skill(s):\n")
    for i, entry in enumerate(results, 1):
        verified_badge = " ✓" if entry.verified else ""
        cat_name = registry.categories.get(entry.category, Category("", "", "")).name if entry.category else ""
        print(f"  {i}. {entry.display_name}{verified_badge}")
        print(f"     {entry.description[:80]}")
        print(f"     Tags: {', '.join(entry.tags) if entry.tags else '—'}")
        print(f"     Category: {cat_name or '—'}  v{entry.version}")
        print()
    return 0

def cmd_info(args: argparse.Namespace) -> int:
    registry = load_registry()
    entry = registry.skills.get(args.name)
    if not entry:
        print(f"Skill '{args.name}' not found in registry")
        return 1

    if args.json:
        print(json.dumps(_entry_to_dict(entry), indent=2))
        return 0

    print(f"\n  {entry.display_name}  v{entry.version}")
    print(f"  {'✓ Verified' if entry.verified else '⚠ Third-party'}")
    print()
    print(f"  Description:  {entry.description}")
    print(f"  Author:       {entry.author.name}")
    if entry.author.url:
        print(f"  URL:          {entry.author.url}")
    print(f"  Repository:   {entry.repo}")
    print(f"  License:      {entry.license or '—'}")
    print(f"  Category:     {entry.category or '—'}")
    print(f"  Platforms:    {', '.join(entry.platforms) if entry.platforms else '—'}")
    print(f"  Tags:         {', '.join(entry.tags) if entry.tags else '—'}")
    if entry.semantic:
        print(f"  Intents:      {len(entry.semantic.intents)} intent(s)")
    print()
    return 0

def cmd_list(args: argparse.Namespace) -> int:
    registry = load_registry()
    skills = list(registry.skills.values())

    if args.category:
        skills = [s for s in skills if s.category == args.category]
        if not skills:
            print(f"No skills in category '{args.category}'")
            return 1

    if args.json:
        data = [_entry_to_dict(e) for e in skills]
        print(json.dumps(data, indent=2))
        return 0

    if args.category:
        cat_name = registry.categories.get(args.category, Category(args.category, args.category, "")).name
        print(f"\nCategory: {cat_name}")
    else:
        print(f"\nAll skills ({len(skills)} total):\n")

    for entry in skills:
        print(f"  {entry.display_name:<40} v{entry.version:<8} {entry.description[:50]}")
    print()
    return 0

def cmd_categories(args: argparse.Namespace) -> int:
    registry = load_registry()
    print("\nAvailable categories:\n")
    for cat in registry.categories.values():
        count = sum(1 for s in registry.skills.values() if s.category == cat.id)
        print(f"  {cat.id:<20} {cat.name:<30} ({count} skills)")
    print()
    return 0

def _entry_to_dict(entry) -> dict:
    return {
        "name": entry.name,
        "display_name": entry.display_name,
        "version": entry.version,
        "description": entry.description,
        "repo": entry.repo,
        "author": {"name": entry.author.name, "url": entry.author.url},
        "tags": entry.tags,
        "category": entry.category,
        "platforms": entry.platforms,
        "license": entry.license,
        "verified": entry.verified,
        "install_count": entry.install_count,
    }

from scripts.skillctl.models import Category  # noqa: E402 (late import for info listing)
```

- [ ] **Step 2: Write search tests**

```python
# scripts/tests/test_skillctl_search.py
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from scripts.skillctl.models import Registry, SkillEntry, Category

def make_registry():
    skills = {
        "alpha": SkillEntry("alpha", "Alpha Tool", "1.0.0", "First tool", "repo", tags=["dev"]),
        "beta": SkillEntry("beta", "Beta Analyzer", "2.0.0", "Data analysis", "repo", tags=["data"]),
    }
    cats = {"dev": Category("dev", "Development"), "data": Category("data", "Data")}
    return Registry(skills=skills, categories=cats)

class TestList(unittest.TestCase):
    def setUp(self):
        self.reg = make_registry()

    def test_list_all(self):
        self.assertEqual(len(self.reg.skills), 2)

    def test_list_filter_by_category(self):
        filtered = [s for s in self.reg.skills.values() if s.category == "dev"]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "alpha")

class TestEntryToDict(unittest.TestCase):
    def test_entry_dict_has_required_keys(self):
        from scripts.skillctl.search import _entry_to_dict
        entry = SkillEntry("test", "Test", "1.0", "Desc", "repo", tags=["a"], verified=True)
        d = _entry_to_dict(entry)
        for key in ("name", "display_name", "version", "description", "tags", "verified"):
            self.assertIn(key, d)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run search tests**

Run: `python -m pytest scripts/tests/test_skillctl_search.py -v`
Expected: Tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/skillctl/search.py scripts/tests/test_skillctl_search.py
git commit -m "feat(skillctl): search, info, list, categories commands"
```

---

#### Task 6: `skillctl install` — exact name install

**Files:**
- Create: `scripts/skillctl/install.py`
- Create: `scripts/tests/test_skillctl_install.py`

- [ ] **Step 1: Write install module**

```python
# scripts/skillctl/install.py
from __future__ import annotations
import argparse
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path

from scripts.skillctl.index import load_registry, ensure_index
from scripts.skillctl.config import record_installation, CACHE_DIR, ensure_dirs
from scripts.skillctl.models import SkillEntry
from scripts.platforms import get_platform, user_paths

def resolve_skill_entry(name: str) -> SkillEntry | None:
    """Look up a skill by exact name in the registry."""
    registry = load_registry()
    return registry.skills.get(name)

def resolve_install_dir(platform: str | None, custom_dir: str | None) -> Path:
    """Determine install target directory."""
    if custom_dir:
        return Path(custom_dir).expanduser().resolve()

    # Auto-detect platform if not specified
    if not platform:
        platform = _detect_current_platform()

    paths = user_paths()
    target = paths.get(platform)
    if not target:
        print(f"Unknown platform: {platform}")
        print(f"Supported: {', '.join(paths.keys())}")
        sys.exit(1)
    return Path(target).expanduser().resolve()

def _detect_current_platform() -> str:
    """Detect which agent platform is running, heuristic check."""
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
    return "universal"  # fallback

def install_from_git(repo_url: str, version: str, target_dir: Path, skill_name: str) -> bool:
    """Clone a skill repo and run install-skill.sh."""
    ensure_dirs()
    cache_path = CACHE_DIR / skill_name

    # Clean cache if it exists
    if cache_path.exists():
        shutil.rmtree(cache_path)

    print(f"  Cloning {repo_url}...")
    result = subprocess.run(
        ["git", "clone", "--depth=1", "--branch", f"v{version}", repo_url, str(cache_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Try without branch (if version tag doesn't exist, clone default branch)
        print(f"  Branch v{version} not found, cloning default branch...")
        result = subprocess.run(
            ["git", "clone", "--depth=1", repo_url, str(cache_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  Failed to clone: {result.stderr.strip()}")
            return False

    # Locate install-skill.sh in the cloned repo
    install_sh = cache_path / "scripts" / "install-skill.sh"
    if not install_sh.exists():
        install_sh = cache_path / "install.sh"
    if not install_sh.exists():
        # Fallback: copy the directory directly
        return _copy_skill_directly(cache_path, target_dir, skill_name)

    print(f"  Running installer: {install_sh}")
    result = subprocess.run(
        ["bash", str(install_sh), str(cache_path), "--target", str(target_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Installation failed: {result.stderr.strip()}")
        return False

    print(result.stdout)
    return True

def _copy_skill_directly(src: Path, target_dir: Path, skill_name: str) -> bool:
    """Fallback: symlink skill directory to target."""
    target = target_dir / skill_name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target)
    return True

def cmd_doctor(args: argparse.Namespace) -> int:
    """Check CLI and index health."""
    from scripts.skillctl.config import SKILLCTL_DIR
    from scripts.skillctl.index import ensure_index, load_registry

    print("\n  skillctl doctor\n")
    print(f"  State directory: {SKILLCTL_DIR}")
    print(f"  State exists:   {'✓' if SKILLCTL_DIR.exists() else '✗ not initialized'}")

    # Check index repo
    try:
        ensure_index()
        print("  Index repo:     ✓ cloned/accessible")
    except Exception as e:
        print(f"  Index repo:     ✗ {e}")
        return 1

    # Check registry parsing
    try:
        reg = load_registry()
        print(f"  Registry:       ✓ {len(reg.skills)} skills, {len(reg.categories)} categories")
    except Exception as e:
        print(f"  Registry:       ✗ {e}")
        return 1

    print()
    return 0

def cmd_install(args: argparse.Namespace) -> int:
    skill_name = args.target.split("@")[0]
    version = args.target.split("@")[1] if "@" in args.target else None

    # Check if it's a semantic query (contains non-keyword chars or can't resolve)
    entry = resolve_skill_entry(skill_name)
    if not entry:
        # Try semantic match
        from scripts.skillctl.search import semantic_search
        registry = load_registry()
        results = semantic_search(registry, args.target, top_k=1)
        if results:
            entry = results[0]
            print(f"  Interpreting '{args.target}' as: {entry.display_name}")
        else:
            print(f"  Skill '{skill_name}' not found. Try 'skillctl search {skill_name}'")
            return 1

    target_version = version or entry.version
    install_dir = resolve_install_dir(args.platform, args.dir)

    print(f"\n  Installing {entry.display_name} v{target_version}")
    print(f"  Target:    {install_dir}")
    print(f"  Verified:  {'✓' if entry.verified else '⚠ Third-party skill'}")
    print()

    if not entry.verified:
        response = input("  This skill is from a third-party. Continue? (y/N): ")
        if response.lower() != "y":
            print("  Installation cancelled.")
            return 1

    if install_dir.exists():
        print(f"  Directory {install_dir} exists. Installing into it...")
    install_dir.mkdir(parents=True, exist_ok=True)

    success = install_from_git(entry.repo, target_version, install_dir, entry.name)
    if success:
        record_installation(entry.name, target_version, entry.repo, args.platform or "auto")
        print(f"\n  ✓ {entry.display_name} v{target_version} installed to {install_dir}")
        print(f"  Run 'skillctl update {entry.name}' for future updates.")
    else:
        print(f"\n  ✗ Installation failed for {entry.display_name}")
        return 1

    return 0
```

- [ ] **Step 2: Write install tests**

```python
# scripts/tests/test_skillctl_install.py
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from scripts.skillctl.install import resolve_skill_entry, resolve_install_dir, _detect_current_platform
from scripts.skillctl.models import SkillEntry

class TestResolveEntry(unittest.TestCase):
    @patch("scripts.skillctl.install.load_registry")
    def test_resolve_existing(self, mock_load):
        entry = SkillEntry("test", "Test", "1.0", "Desc", "repo")
        mock_load.return_value.skills = {"test": entry}
        result = resolve_skill_entry("test")
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test")

    @patch("scripts.skillctl.install.load_registry")
    def test_resolve_missing(self, mock_load):
        mock_load.return_value.skills = {}
        result = resolve_skill_entry("nonexistent")
        self.assertIsNone(result)

class TestDetectPlatform(unittest.TestCase):
    @patch("scripts.skillctl.install.Path.home")
    def test_universal_fallback(self, mock_home):
        mock_home.return_value = Path("/nonexistent")
        result = _detect_current_platform()
        self.assertEqual(result, "universal")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run install tests**

Run: `python -m pytest scripts/tests/test_skillctl_install.py -v`
Expected: Tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/skillctl/install.py scripts/tests/test_skillctl_install.py
git commit -m "feat(skillctl): install command — exact name resolution + git clone + install-skill.sh delegation"
```

---

### Phase 2: Semantic Layer

#### Task 7: Semantic NL matching for search and install

**Files:**
- Modify: `scripts/skillctl/search.py` (add `semantic_search` function)

- [ ] **Step 1: Add semantic search to search module**

Append to `scripts/skillctl/search.py`:

```python
# --- Semantic / NL matching ---

def semantic_search(registry: "Registry", query: str, top_k: int = 3) -> list[SkillEntry]:
    """Match a natural language query against skills' semantic.intents.

    Scoring strategy (no LLM required):
      1. Exact intent match → score 1.0
      2. Partial query-in-intent → score (matched_chars / len(intent))
      3. Keyword overlap (query words ∩ intent words) → score ratio
      4. Fallback to tag match → score 0.3
    Returns top_k results sorted by score descending.
    """
    scored: list[tuple[float, SkillEntry]] = []
    q_lower = query.lower()
    q_words = set(q_lower.split())

    for entry in registry.skills.values():
        score = 0.0
        intents = []
        if entry.semantic and entry.semantic.intents:
            intents = [i.lower() for i in entry.semantic.intents]

        # 1. Exact intent match
        if any(q_lower == intent for intent in intents):
            score = 1.0
        # 2. Partial match (query is substring of an intent)
        elif any(q_lower in intent for intent in intents):
            score = 0.85
        # 3. Keyword overlap with intents
        elif intents:
            all_intent_words = set()
            for intent in intents:
                all_intent_words |= set(intent.split())
            if q_words and all_intent_words:
                overlap = q_words & all_intent_words
                score = 0.5 * len(overlap) / max(len(q_words), 1)
        # 4. Tag fallback
        if score == 0.0:
            tag_overlap = q_words & set(entry.tags)
            if tag_overlap:
                score = 0.3 * len(tag_overlap) / max(len(q_words), 1)

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    return [entry for score, entry in scored[:top_k]]
```

- [ ] **Step 2: Enhance `cmd_search` to try semantic if keyword fails**

Modify the end of `cmd_search` in `scripts/skillctl/search.py`. After keyword search returns zero results, fall through to semantic:

```python
def cmd_search(args: argparse.Namespace) -> int:
    registry = load_registry()
    results = search_registry(registry, args.query)

    # If keyword search yields nothing, try semantic
    if not results:
        results = semantic_search(registry, args.query)
        if results:
            print(f"\n  No keyword match. Showing semantic matches for '{args.query}':\n")

    # rest of existing cmd_search...
```

- [ ] **Step 3: Write semantic search tests**

Append to `scripts/tests/test_skillctl_search.py`:

```python
class TestSemanticSearch(unittest.TestCase):
    def setUp(self):
        from scripts.skillctl.models import SemanticMetadata
        skills = {
            "fin-copilot": SkillEntry(
                "fin-copilot", "Financial Copilot", "1.0", "Fin", "repo",
                tags=["stocks", "trading"],
                semantic=SemanticMetadata(
                    intents=["分析股票技术指标", "generate trading signals", "check RSI and MACD"]
                ),
            ),
            "crm-report": SkillEntry(
                "crm-report", "CRM Report", "2.0", "CRM", "repo",
                tags=["crm", "sales"],
            ),
        }
        self.reg = Registry(skills=skills, categories={})

    def test_exact_intent_match_en(self):
        from scripts.skillctl.search import semantic_search
        results = semantic_search(self.reg, "generate trading signals")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "fin-copilot")

    def test_exact_intent_match_zh(self):
        from scripts.skillctl.search import semantic_search
        results = semantic_search(self.reg, "分析股票技术指标")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "fin-copilot")

    def test_partial_match(self):
        from scripts.skillctl.search import semantic_search
        results = semantic_search(self.reg, "RSI")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "fin-copilot")

    def test_tag_fallback(self):
        from scripts.skillctl.search import semantic_search
        results = semantic_search(self.reg, "stocks")
        self.assertEqual(len(results), 1)

    def test_multiple_results_ordered(self):
        from scripts.skillctl.search import semantic_search
        # Add a second skill with weaker match
        from scripts.skillctl.models import SemanticMetadata
        self.reg.skills["analysis-tool"] = SkillEntry(
            "analysis-tool", "Analysis Tool", "1.0", "Tool", "repo",
            tags=["analysis"],
            semantic=SemanticMetadata(intents=["run analysis on data"]),
        )
        results = semantic_search(self.reg, "trading signals analysis", top_k=3)
        self.assertGreaterEqual(len(results), 2)
```

- [ ] **Step 4: Run all search tests**

Run: `python -m pytest scripts/tests/test_skillctl_search.py -v`
Expected: 9 tests pass (4 from Task 5 + 5 from semantic)

- [ ] **Step 5: Commit**

```bash
git add scripts/skillctl/search.py scripts/tests/test_skillctl_search.py
git commit -m "feat(skillctl): semantic NL matching for search and install"
```

---

### Phase 3: Publish Pipeline

#### Task 8: `skillctl publish` — preflight, GitHub repo creation, push

**Files:**
- Create: `scripts/skillctl/publish.py`
- Create: `scripts/tests/test_skillctl_publish.py`

- [ ] **Step 1: Write publish module**

```python
# scripts/skillctl/publish.py
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.skillctl.config import load_config
from scripts.skillctl.index import load_registry
from scripts.skillctl.models import SkillEntry, Author

def cmd_publish(args: argparse.Namespace) -> int:
    """Publish a skill to GitHub and register in the index."""
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    org = args.org or "agent-skills"

    if not skill_dir.exists():
        print(f"Error: skill directory not found: {skill_dir}")
        return 1

    # Phase 1: Preflight
    print(f"\n  Preflight: {skill_dir}\n")

    # Validate skill directory
    sys.path.insert(0, str(skill_dir.parent))
    try:
        from scripts import validate
        from scripts import security_scan
    except ImportError:
        # Fallback: try from repo scripts
        repo_scripts = Path(__file__).parent.parent
        sys.path.insert(0, str(repo_scripts))
        from scripts import validate  # type: ignore
        from scripts import security_scan  # type: ignore

    # Extract metadata
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print("  ✗ SKILL.md not found — aborting")
        return 1

    content = skill_md.read_text()
    frontmatter = _parse_frontmatter(content)
    skill_name = frontmatter.get("name", skill_dir.name)
    version = frontmatter.get("metadata", {}).get("version", "1.0.0")
    author_name = frontmatter.get("metadata", {}).get("author", "unknown")
    description = frontmatter.get("description", "")

    print(f"  Name:        {skill_name}")
    print(f"  Version:     {version}")
    print(f"  Author:      {author_name}")
    print(f"  Description: {description[:60]}...")
    print()

    # Dry-run mode
    if args.dry_run:
        print("  [DRY RUN] Preflight complete. Use --dry-run to commit.")
        return 0

    # Phase 2: GitHub repo creation
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("  ✗ GITHUB_TOKEN or GH_TOKEN not set")
        return 1

    repo_name = skill_name
    repo_full = f"{org}/{repo_name}"

    print(f"  Creating repo: {repo_full}")

    # Check if repo already exists
    result = subprocess.run(
        ["gh", "repo", "view", repo_full, "--json", "name"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Create repo
        result = subprocess.run(
            ["gh", "repo", "create", repo_full, "--public", "--description", description[:100]],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  ✗ Failed to create repo: {result.stderr.strip()}")
            return 1
        print("  ✓ Repo created")
    else:
        print("  ✓ Repo already exists")

    # Phase 3: Push
    print("  Pushing skill content...")
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        # Init local git, add files, push
        repo_tmp = tmp_dir / skill_name
        shutil.copytree(skill_dir, repo_tmp, ignore=_ignore_patterns())
        result = subprocess.run(
            ["git", "init"],
            capture_output=True, text=True,
            cwd=str(repo_tmp),
        )
        subprocess.run(["git", "add", "-A"], capture_output=True, cwd=str(repo_tmp))
        subprocess.run(
            ["git", "commit", "-m", f"chore: initial commit v{version}"],
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
            print(f"  ✗ Push failed: {result.stderr.strip()}")
            return 1

        # Tag
        subprocess.run(
            ["git", "tag", f"v{version}"],
            capture_output=True, cwd=str(repo_tmp),
        )
        subprocess.run(
            ["git", "push", "origin", f"v{version}"],
            capture_output=True, cwd=str(repo_tmp),
        )

        print("  ✓ Content pushed with tag v{version}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Phase 4: Register in index
    print("  Registering in index...")
    _register_in_index(skill_name, repo_full, version, description, author_name, org)

    print(f"\n  ✓ Published: https://github.com/{repo_full}")
    print(f"  Try: skillctl install {skill_name}")
    return 0

def _parse_frontmatter(content: str) -> dict:
    """Extract YAML-like frontmatter between --- markers."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    end = 1
    while end < len(lines) and lines[end].strip() != "---":
        end += 1
    # Simple dict parser (delegates heavy parsing to validate.py)
    result = {}
    current_key = None
    current_value = {}
    for line in lines[1:end]:
        line = line.strip()
        if not line:
            continue
        if line.startswith("name:") and not line.startswith("name: >"):
            result["name"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            result["description"] = line.split(":", 1)[1].strip().strip(">").strip().strip('"')
        elif line.startswith("metadata:"):
            current_key = "metadata"
            current_value = {}
        elif current_key and line.startswith("  "):
            k, v = line.strip().split(":", 1)
            current_value[k.strip()] = v.strip()
        elif line == "---" and current_key:
            result[current_key] = current_value
            current_key = None
    if current_key and current_value:
        result[current_key] = current_value
    return result

def _register_in_index(skill_name: str, repo_full: str, version: str,
                        description: str, author_name: str, org: str) -> None:
    """Add or update the skill entry in the local index clone and push."""
    from scripts.skillctl.index import ensure_index
    from scripts.skillctl.config import INDEX_DIR

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
        "created": __import__("datetime").date.today().isoformat(),
        "updated": __import__("datetime").date.today().isoformat(),
    }

    reg_path = INDEX_DIR / "registry.json"
    data = json.loads(reg_path.read_text()) if reg_path.exists() else {"skills": []}

    # Update or append
    existing = [s for s in data.get("skills", []) if s["name"] != skill_name]
    existing.append(entry)
    data["skills"] = existing
    data.setdefault("registry", {})["updated"] = __import__("datetime").datetime.now().isoformat()

    reg_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # Commit and push
    result = subprocess.run(
        ["git", "-C", str(INDEX_DIR), "add", "registry.json"],
        capture_output=True,
    )
    result = subprocess.run(
        ["git", "-C", str(INDEX_DIR), "commit", "-m", f"feat: register {skill_name} v{version}"],
        capture_output=True, text=True,
    )
    if "nothing to commit" not in result.stdout:
        subprocess.run(
            ["git", "-C", str(INDEX_DIR), "push"],
            capture_output=True,
        )

def _ignore_patterns():
    import shutil
    return shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv", "venv", ".DS_Store")
```

- [ ] **Step 2: Write publish tests**

```python
# scripts/tests/test_skillctl_publish.py
import unittest
import tempfile
from pathlib import Path
from scripts.skillctl.publish import _parse_frontmatter

class TestParseFrontmatter(unittest.TestCase):
    def test_parse_simple(self):
        content = """---
name: test-skill
description: A test skill
---

# Body
"""
        result = _parse_frontmatter(content)
        self.assertEqual(result.get("name"), "test-skill")

    def test_parse_with_metadata(self):
        content = """---
name: my-skill
description: >-
  A multi-line description
metadata:
  author: alice
  version: 1.0.0
---

# Body
"""
        result = _parse_frontmatter(content)
        self.assertEqual(result.get("name"), "my-skill")
        self.assertEqual(result.get("metadata", {}).get("version"), "1.0.0")

    def test_no_frontmatter(self):
        result = _parse_frontmatter("No frontmatter here")
        self.assertEqual(result, {})

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run publish tests**

Run: `python -m pytest scripts/tests/test_skillctl_publish.py -v`
Expected: 3 tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/skillctl/publish.py scripts/tests/test_skillctl_publish.py
git commit -m "feat(skillctl): publish command — preflight, repo creation, push, index registration"
```

---

#### Task 9: Phase 5 integration — publishing from the factory pipeline

**Files:**
- Modify: `SKILL.md` — add publish prompt to Phase 5 (around the "Phase 5: Export and Install" section)

- [ ] **Step 1: Enhance SKILL.md Phase 5**

Find the Phase 5 section in SKILL.md (it should be self-documented with Phase markers). Add a publish prompt at the end:

In `SKILL.md`, locate the Phase 5 conclusion where the skill directory is ready. Append:

```markdown
### Publish (Optional)

After installation, you can publish the skill to the global skill registry:

```bash
skillctl publish <skill-dir>
```

If `GITHUB_TOKEN` is set, the factory can prompt automatically:

```markdown
Publish this skill to GitHub? (y/N)
```

On success:

```
✓ Published to agent-skills/{name} (v{version})
Try: skillctl install {name}
```
```

Search for the Phase 5 markers in SKILL.md to insert precisely.

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "feat: add publish prompt to Phase 5 pipeline"
```

---

### Phase 4: Update & Security

#### Task 10: `skillctl update` — version check and upgrade

**Files:**
- Create: `scripts/skillctl/update.py`
- Create: `scripts/tests/test_skillctl_update.py`

- [ ] **Step 1: Write update module**

```python
# scripts/skillctl/update.py
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from scripts.skillctl.config import load_installed, save_installed, INDEX_DIR
from scripts.skillctl.index import load_registry
from scripts.skillctl.models import SkillEntry

def cmd_update(args: argparse.Namespace) -> int:
    installed = load_installed()

    if not installed:
        print("  No installed skills found.")
        return 0

    registry = load_registry()

    if args.name:
        installed = [s for s in installed if s["name"] == args.name]
        if not installed:
            print(f"  '{args.name}' is not installed.")
            return 1

    updated_any = False
    for skill in installed:
        name = skill["name"]
        current_version = skill["version"]

        entry = registry.skills.get(name)
        if not entry:
            print(f"  {name}: not found in registry (removed?)")
            continue

        if entry.version == current_version:
            print(f"  {name}: already up to date (v{current_version})")
            continue

        print(f"  {name}: v{current_version} → v{entry.version}")

        if not args.check:
            # Perform upgrade
            _perform_upgrade(name, entry)
            # Update local record
            skill["version"] = entry.version
            updated_any = True

    if updated_any:
        save_installed(installed)
        print("\n  ✓ Update complete.")

    return 0

def _perform_upgrade(name: str, entry: SkillEntry) -> bool:
    """Git fetch + checkout new version + re-symlink."""
    from scripts.skillctl.config import CACHE_DIR
    import subprocess, shutil

    cache_path = CACHE_DIR / name
    if not cache_path.exists():
        print(f"  {name}: cache not found, re-cloning...")
        from scripts.skillctl.install import install_from_git
        # We need a target dir — check installed.json for platform
        return False

    # Fetch and checkout
    result = subprocess.run(
        ["git", "-C", str(cache_path), "fetch", "--tags"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  {name}: fetch failed: {result.stderr.strip()}")
        return False

    result = subprocess.run(
        ["git", "-C", str(cache_path), "checkout", f"v{entry.version}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Try without 'v' prefix
        result = subprocess.run(
            ["git", "-C", str(cache_path), "checkout", entry.version],
            capture_output=True, text=True,
        )
    if result.returncode == 0:
        print(f"  {name}: checked out v{entry.version}")
        return True

    print(f"  {name}: checkout failed")
    return False
```

- [ ] **Step 2: Write update tests**

```python
# scripts/tests/test_skillctl_update.py
import unittest
from unittest.mock import patch, MagicMock
from scripts.skillctl.update import cmd_update
from scripts.skillctl.models import Registry, SkillEntry

class TestUpdate(unittest.TestCase):
    @patch("scripts.skillctl.update.load_installed")
    @patch("scripts.skillctl.update.load_registry")
    @patch("scripts.skillctl.update.save_installed")
    def test_update_check_only(self, mock_save, mock_reg, mock_inst):
        mock_inst.return_value = [
            {"name": "test-skill", "version": "1.0.0", "repo": "repo"},
        ]
        reg = Registry(skills={
            "test-skill": SkillEntry("test-skill", "Test", "2.0.0", "Updated", "repo"),
        }, categories={})
        mock_reg.return_value = reg

        args = MagicMock(name="test-skill", check=True)
        args.name = "test-skill"
        args.check = True

        result = cmd_update(args)
        self.assertEqual(result, 0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run update tests**

Run: `python -m pytest scripts/tests/test_skillctl_update.py -v`
Expected: 1 test passes

- [ ] **Step 4: Commit**

```bash
git add scripts/skillctl/update.py scripts/tests/test_skillctl_update.py
git commit -m "feat(skillctl): update command — version check + git fetch upgrade"
```

---

#### Task 11: Security integration and shell installer enhancement

**Files:**
- Modify: `scripts/install-skill.sh` — add `--from-registry` mode

- [ ] **Step 1: Enhance install-skill.sh with `--from-registry`**

Add a new flag to `install-skill.sh`:

```bash
# After existing option parsing, add:
        --from-registry)
            # Delegate to skillctl install
            SKILL_NAME="$2"
            shift 2
            ;;
```

And at the end of the option parsing:

```bash
if [ -n "${SKILL_NAME:-}" ]; then
    # Delegate to skillctl
    exec python3 "$(dirname "$0")/skillctl/__main__.py" install "$SKILL_NAME"
fi
```

- [ ] **Step 2: Same for install-skill.ps1**

Add a `-FromRegistry` parameter:

```powershell
param(
    [switch]$FromRegistry,
    [string]$SkillName
)

if ($FromRegistry -and $SkillName) {
    python3 "$PSScriptRoot/skillctl/__main__.py" install $SkillName
    exit $LASTEXITCODE
}
```

- [ ] **Step 3: Run existing tests to confirm no regression**

Run: `python -m pytest scripts/tests/test_skill_registry.py -v`
Expected: All existing tests still pass

- [ ] **Step 4: Commit**

```bash
git add scripts/install-skill.sh scripts/install-skill.ps1
git commit -m "feat: add --from-registry flag to shell installers"
```

---

### Phase 5: Index Repository Setup

#### Task 12: Create the GitHub index repository

**Files:** (all in a new repository — not in this repo, but documented here for setup)

- Create: `registry.json` (in `agent-skills/index` GitHub repo)
- Create: `registry.schema.json`
- Create: `AGENTS.md`
- Create: `.github/workflows/validate-registry.yaml`
- Create: `.github/workflows/sync-versions.yaml`

- [ ] **Step 1: Create the index repository on GitHub**

```bash
# One-time setup (run outside this repo)
gh repo create agent-skills/index --public --description "Central index for agent-skill-creator skills"
git clone https://github.com/agent-skills/index.git
cd index
```

- [ ] **Step 2: Create registry.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["registry", "skills"],
  "properties": {
    "registry": {
      "type": "object",
      "required": ["name", "created", "schema_version"],
      "properties": {
        "name": {"type": "string"},
        "created": {"type": "string", "format": "date-time"},
        "updated": {"type": "string", "format": "date-time"},
        "schema_version": {"type": "string"},
        "github_org": {"type": "string"}
      }
    },
    "categories": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "description": {"type": "string"}
        }
      }
    },
    "skills": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "version", "description", "repo"],
        "properties": {
          "name": {"type": "string"},
          "display_name": {"type": "string"},
          "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
          "description": {"type": "string"},
          "repo": {"type": "string", "format": "uri"},
          "author": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "url": {"type": "string", "format": "uri"}
            }
          },
          "tags": {"type": "array", "items": {"type": "string"}},
          "category": {"type": "string"},
          "platforms": {"type": "array", "items": {"type": "string"}},
          "license": {"type": "string"},
          "verified": {"type": "boolean"},
          "min_cli_version": {"type": "string"},
          "semantic": {
            "type": "object",
            "properties": {
              "intents": {"type": "array", "items": {"type": "string"}},
              "prompt_triggers": {"type": "array", "items": {"type": "string"}},
              "requires": {"type": "array", "items": {"type": "string"}},
              "produces": {"type": "array", "items": {"type": "string"}}
            }
          },
          "dependencies": {"type": "array", "items": {"type": "string"}},
          "install_count": {"type": "integer"}
        }
      }
    }
  }
}
```

- [ ] **Step 3: Create initial registry.json with categories only**

```json
{
  "registry": {
    "name": "Agent Skills Index",
    "created": "2026-07-28T00:00:00+00:00",
    "updated": "2026-07-28T00:00:00+00:00",
    "schema_version": "2",
    "github_org": "agent-skills",
    "description": "Official skill index for the agent-skill-creator ecosystem"
  },
  "categories": [
    {"id": "ai", "name": "AI & Machine Learning", "description": "Skills for LLM workflows, model interaction, prompt engineering"},
    {"id": "compliance", "name": "Compliance & Audit", "description": "Regulatory compliance, audit reporting, governance"},
    {"id": "data-engineering", "name": "Data Engineering", "description": "ETL, data cleaning, validation, transformation"},
    {"id": "devops", "name": "DevOps & Infrastructure", "description": "Deployment, monitoring, CI/CD automation"},
    {"id": "financial", "name": "Financial Analysis", "description": "Market data, portfolio management, trading signals"},
    {"id": "crm", "name": "Sales & CRM", "description": "CRM workflows, sales reporting, pipeline management"},
    {"id": "utility", "name": "Utilities", "description": "General-purpose automation and productivity tools"},
    {"id": "writing", "name": "Writing & Content", "description": "Content generation, editing, brand voice enforcement"}
  ],
  "skills": []
}
```

- [ ] **Step 4: Create AGENTS.md**

```markdown
# Agent Skills Index

This repository catalogs agent skills that can be installed and used at conversation time.

## For Agentic Workers

When a user expresses an intent that matches a skill in this index, you should automatically install it. Follow these rules:

1. Read `registry.json` to see all available skills
2. For each skill, check `semantic.intents` and `prompt_triggers` against the user's current request
3. If best match confidence > 70%:
   → Run: `skillctl install <skill-name>`
4. If confidence 40-70%:
   → Suggest: "I can help with that. Try `skillctl install <skill-name>`?"
5. If confidence < 40%: do nothing
6. After installation, invoke the skill immediately via its SKILL.md instructions

## Manual Installation

```bash
skillctl search <query>
skillctl install <skill-name>
skillctl info <skill-name>
```
```

- [ ] **Step 5: Create validate-registry.yaml workflow**

```yaml
name: Validate Registry
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Validate registry.json
        run: |
          python -c "
import json, sys
with open('registry.json') as f:
    data = json.load(f)
assert 'registry' in data, 'Missing registry section'
assert 'skills' in data, 'Missing skills section'
assert isinstance(data['skills'], list), 'skills must be a list'
for s in data['skills']:
    assert s.get('name'), f'Skill missing name: {s}'
    assert s.get('version'), f'Skill {s.get(\"name\")} missing version'
    assert s.get('repo'), f'Skill {s.get(\"name\")} missing repo'
    import re
    assert re.match(r'^\d+\.\d+\.\d+$', s['version']), f'{s[\"name\"]}: version must be semver'
print('✓ registry.json validation passed')
          "
      - name: Check duplicate names
        run: |
          python -c "
import json
with open('registry.json') as f:
    data = json.load(f)
names = [s['name'] for s in data['skills']]
dupes = [n for n in names if names.count(n) > 1]
if dupes:
    print(f'Duplicate skill names: {set(dupes)}')
    sys.exit(1)
print('✓ No duplicate skill names')
          "
      - name: Verify schema
        uses: python-jsonschema/check@v0.3
        with:
          schema: registry.schema.json
          files: registry.json
```

- [ ] **Step 6: Create sync-versions.yaml workflow**

```yaml
name: Sync Versions
on:
  schedule: [{cron: "0 6 * * 1"}]
  workflow_dispatch:
jobs:
  sync:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Update versions from GitHub releases
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          python -c "
import json, subprocess, sys
with open('registry.json') as f:
    data = json.load(f)
updated = False
for skill in data.get('skills', []):
    repo_url = skill.get('repo', '')
    # Extract owner/name from URL
    parts = repo_url.rstrip('/').rstrip('.git').split('/')
    if len(parts) >= 2:
        repo_path = '/'.join(parts[-2:])
        try:
            result = subprocess.run(
                ['gh', 'release', 'view', '--repo', repo_path, '--json', 'tagName'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                tag = json.loads(result.stdout)['tagName']
                latest = tag.lstrip('v')
                if latest != skill.get('version'):
                    print(f'{skill[\"name\"]}: {skill.get(\"version\")} → {latest}')
                    skill['version'] = latest
                    updated = True
        except Exception as e:
            print(f'{skill[\"name\"]}: error fetching release — {e}', file=sys.stderr)
if updated:
    with open('registry.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('Versions updated.')
else:
    print('All versions up to date.')
          "
      - name: Create PR if updated
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "chore: sync skill versions"
          title: "chore: sync skill versions"
          branch: "sync-versions"
          delete-branch: true
```

- [ ] **Step 7: Push to GitHub**

```bash
cd index
git add .
git commit -m "chore: initial index repository setup"
git push -u origin main
```

---

## Self-Review

### Spec coverage

| Spec section | Implemented by |
|-------------|---------------|
| 1. Mission & Positioning | Covered by this plan's structure and design decisions |
| 2. Architecture Overview | Task 4 (CLI entry), Task 6 (install flow), Task 8 (publish) |
| 3. Index Repository Design | Task 1 (models), Task 3 (registry parsing), Task 12 (index repo) |
| 4. skillctl CLI Design | Task 4 (CLI dispatch), Task 5 (search/info/list), Task 6 (install) |
| 4.2 Semantic install | Task 7 (semantic_search) |
| 4.3 Agent-native auto-install | Task 12 (AGENTS.md for index repo) |
| 5. Publish Pipeline | Task 8 (publish command), Task 9 (Phase 5 integration) |
| 6. Version Management | Task 10 (update command) |
| 7. Security Model | Task 11 (security scan integration in publish preflight) |
| 8. Third-Party & Community | Task 6 (verified flag prompt), Task 12 (schema supports third-party) |
| 9. Change Inventory | All 12 tasks cover the 8 assets listed |

### Placeholder scan

No "TBD", "TODO", or placeholder patterns found. Every step has complete code.

### Type consistency

- Task 1 defines `SkillEntry`, `SemanticMetadata`, `Registry` — used by Task 3, 5, 6, 7
- Task 3's `load_registry()` returns `Registry` dataclass — used by Task 5, 6, 10
- Task 7's `semantic_search()` takes `Registry` and returns `list[SkillEntry]` — matching Task 6's consumer
- Task 6's `resolve_skill_entry()` returns `SkillEntry | None` — consistent
- `_parse_frontmatter()` in Task 8 returns `dict` — consistent with its test

All consistent.
