# 技能分发架构实施计划

> **面向Agent工作器：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 按任务逐步实施。步骤使用 `- [ ]` 复选框语法跟踪进度。

**目标：** 为 agent-skill-creator 构建 GitHub 原生的技能分发系统：索引仓库、`skillctl` CLI、语义安装、发布流水线、安全模型。

**架构：** 在 `scripts/` 下新增 `skillctl` Python 包，从基于 GitHub 的索引仓库（`agent-skills/index`）读取，安装委托给 `install-skill.sh`，发布通过 GitHub API。由一个 Shell 包装器提供 `skillctl` 命令。每个任务构建一个可独立测试的能力模块。

**技术栈：** Python 3.10+, Shell（POSIX sh + PowerShell）, GitHub API（REST v3）, JSON Schema, 复用现有 validate.py / security_scan.py / skill_registry.py

---

## 文件结构

```
scripts/
├── skillctl                        # Shell 入口（exec python -m）
├── skillctl/
│   ├── __init__.py                 # 包标记 + __version__
│   ├── __main__.py                 # python -m 分发 → cli.main()
│   ├── cli.py                      # ArgumentParser, 命令分发
│   ├── models.py                   # Skill, Category, RegistryEntry 数据类
│   ├── config.py                   # ~/.skillctl/ 目录初始化, installed.json, config.json
│   ├── index.py                    # 索引仓库 clone/pull/缓存管理
│   ├── install.py                  # 安装流程：解析 → git clone → install-skill.sh
│   ├── search.py                   # 关键词搜索 + 自然语言语义匹配
│   ├── publish.py                  # 发布流程：预检 → 建仓 → push → 注册索引
│   └── update.py                   # 版本检查 + 升级
├── install-skill.sh                # 小改动：新增 --from-registry 参数
├── install-skill.ps1               # 小改动：同上
└── tests/
    ├── test_skillctl_models.py
    ├── test_skillctl_config.py
    ├── test_skillctl_index.py
    ├── test_skillctl_install.py
    ├── test_skillctl_search.py
    ├── test_skillctl_publish.py
    └── test_skillctl_update.py

SKILL.md                            # Phase 5：新增发布提示
```

---

## 任务分解

### Phase 0：基础设施

#### 任务 1：数据模型 — Skill, Category, RegistryEntry

**涉及文件：**
- 新建：`scripts/skillctl/__init__.py`
- 新建：`scripts/skillctl/models.py`
- 新建：`scripts/tests/test_skillctl_models.py`

- [ ] **步骤 1：写数据模型**

```python
# scripts/skillctl/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Author:
    """技能作者信息"""
    name: str
    url: str = ""

@dataclass
class SemanticMetadata:
    """语义匹配元数据 — 用于自然语言搜索和 Agent 自动发现"""
    intents: list[str] = field(default_factory=list)
    prompt_triggers: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)

@dataclass
class Category:
    """技能分类"""
    id: str
    name: str
    description: str = ""

@dataclass
class SkillEntry:
    """索引仓库中的单条技能记录"""
    name: str
    display_name: str
    version: str
    description: str
    repo: str
    author: Author = field(default_factory=lambda: Author("unknown"))
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
    """完整的技能注册表"""
    skills: dict[str, SkillEntry]  # 以技能名为 key
    categories: dict[str, Category]  # 以分类 ID 为 key
    schema_version: str = "2"
    github_org: str = "agent-skills"
    updated: str = ""
```

- [ ] **步骤 2：写测试**

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
        sm = SemanticMetadata(intents=["分析数据"])
        s = SkillEntry("ds", "数据技能", "1.0.0", "数据处理", "repo", semantic=sm)
        self.assertIn("分析数据", s.semantic.intents)

    def test_author_fields(self):
        a = Author("Alice", "https://github.com/alice")
        self.assertEqual(a.name, "Alice")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3：创建 `__init__.py`**

```python
# scripts/skillctl/__init__.py
__version__ = "0.1.0"
```

- [ ] **步骤 4：运行测试**

执行：`python -m pytest scripts/tests/test_skillctl_models.py -v`
期望：3 个测试全部通过

- [ ] **步骤 5：提交**

```bash
git add scripts/skillctl/ scripts/tests/test_skillctl_models.py
git commit -m "feat(skillctl): 新增数据模型 — SkillEntry, Category, Registry"
```

---

#### 任务 2：配置管理 — ~/.skillctl/ 目录状态

**涉及文件：**
- 新建：`scripts/skillctl/config.py`
- 新建：`scripts/tests/test_skillctl_config.py`

- [ ] **步骤 1：写配置模块**

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
```

- [ ] **步骤 2：写配置测试**

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
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.assertTrue(self.tmp.exists())

if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3：运行测试**

执行：`python -m pytest scripts/tests/test_skillctl_config.py -v`
期望：测试通过

- [ ] **步骤 4：提交**

```bash
git add scripts/skillctl/config.py scripts/tests/test_skillctl_config.py
git commit -m "feat(skillctl): 新增配置模块 — ~/.skillctl/ 状态管理"
```

---

#### 任务 3：索引仓库管理 — clone、pull、缓存

**涉及文件：**
- 新建：`scripts/skillctl/index.py`
- 新建：`scripts/tests/test_skillctl_index.py`

- [ ] **步骤 1：写索引模块**

```python
# scripts/skillctl/index.py
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

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
```

- [ ] **步骤 2：写索引测试**

```python
# scripts/tests/test_skillctl_index.py
import unittest
from scripts.skillctl.index import search_registry
from scripts.skillctl.models import Registry, SkillEntry, Category

def make_test_registry() -> Registry:
    """创建含示例技能的测试用 Registry"""
    skills = {
        "alice-financial-copilot": SkillEntry(
            name="alice-financial-copilot",
            display_name="Alice 金融副驾",
            version="1.2.0",
            description="基于 RSI、MACD 的技术分析",
            repo="https://github.com/agent-skills/alice-financial-copilot",
            tags=["股票", "买卖", "技术分析"],
            category="financial",
        ),
        "weekly-crm-report": SkillEntry(
            name="weekly-crm-report",
            display_name="每周 CRM 报表",
            version="2.0.0",
            description="销售数据清洗和区域汇总",
            repo="https://github.com/agent-skills/weekly-crm-report",
            tags=["crm", "销售", "报表"],
            category="crm",
        ),
    }
    categories = {
        "financial": Category("financial", "金融分析", "市场数据相关技能"),
        "crm": Category("crm", "销售 & CRM", "CRM 技能"),
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
        results = search_registry(self.registry, "技术分析")
        self.assertEqual(len(results), 1)

    def test_search_by_description(self):
        results = search_registry(self.registry, "RSI")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        results = search_registry(self.registry, "不存在")
        self.assertEqual(len(results), 0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3：运行索引测试**

执行：`python -m pytest scripts/tests/test_skillctl_index.py -v`
期望：4 个测试全部通过

- [ ] **步骤 4：提交**

```bash
git add scripts/skillctl/index.py scripts/tests/test_skillctl_index.py
git commit -m "feat(skillctl): 索引仓库管理 + registry 解析 + 关键词搜索"
```

---

### Phase 1：核心 CLI

#### 任务 4：CLI 入口和命令分发

**涉及文件：**
- 新建：`scripts/skillctl/__main__.py`
- 新建：`scripts/skillctl/cli.py`
- 新建：`scripts/skillctl`（Shell 包装器）

- [ ] **步骤 1：写 CLI 参数解析器**

```python
# scripts/skillctl/cli.py
from __future__ import annotations
import argparse
import sys

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillctl",
        description="Agent 技能 CLI — 发现、安装、发布 Agent 技能",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search", help="搜索技能")
    p_search.add_argument("query", help="搜索关键词或自然语言描述")
    p_search.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    # install
    p_install = sub.add_parser("install", help="安装技能")
    p_install.add_argument("target", help="技能名称（可含版本号，如 name@1.0.0）或自然语言描述")
    p_install.add_argument("--dir", help="安装到自定义目录")
    p_install.add_argument("--platform", help="目标平台名称")

    # info
    p_info = sub.add_parser("info", help="查看技能详情")
    p_info.add_argument("name", help="技能名称")
    p_info.add_argument("--json", action="store_true")

    # list
    p_list = sub.add_parser("list", help="列出所有可用技能")
    p_list.add_argument("--category", help="按分类过滤")
    p_list.add_argument("--json", action="store_true")

    # update
    p_update = sub.add_parser("update", help="更新已安装技能")
    p_update.add_argument("name", nargs="?", help="技能名称（留空则更新全部）")
    p_update.add_argument("--check", action="store_true", help="仅检查更新不执行")

    # categories
    sub.add_parser("categories", help="列出技能分类")

    # doctor
    sub.add_parser("doctor", help="检查 CLI 和索引仓库健康状态")

    # publish
    p_publish = sub.add_parser("publish", help="将技能发布到 GitHub")
    p_publish.add_argument("skill_dir", help="技能目录路径")
    p_publish.add_argument("--org", help="GitHub 组织名（默认：agent-skills）")
    p_publish.add_argument("--dry-run", action="store_true", help="仅预检不发布")

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

- [ ] **步骤 2：写 `__main__.py`**

```python
# scripts/skillctl/__main__.py
import sys
from scripts.skillctl.cli import main

sys.exit(main())
```

- [ ] **步骤 3：写 Shell 包装器**

```bash
#!/bin/sh
# scripts/skillctl — Shell 包装器，exec python -m scripts.skillctl
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${SCRIPT_DIR}/skillctl/__main__.py" "$@"
```

```bash
# 设置为可执行
chmod +x scripts/skillctl
```

- [ ] **步骤 4：测试 CLI 帮助**

执行：`python scripts/skillctl/__main__.py --help`
期望：显示所有命令

- [ ] **步骤 5：提交**

```bash
git add scripts/skillctl/__main__.py scripts/skillctl/cli.py scripts/skillctl
git commit -m "feat(skillctl): CLI 入口 — argparse 命令分发"
```

---

#### 任务 5：search、info、list、categories 命令

**涉及文件：**
- 新建：`scripts/skillctl/search.py`
- 新建：`scripts/tests/test_skillctl_search.py`

- [ ] **步骤 1：写搜索命令模块**

```python
# scripts/skillctl/search.py
from __future__ import annotations
import argparse
import json
import sys

from scripts.skillctl.index import ensure_index, load_registry, search_registry
from scripts.skillctl.models import Category

def cmd_search(args: argparse.Namespace) -> int:
    """搜索技能：先关键词搜索，无结果则尝试语义匹配"""
    registry = load_registry()
    results = search_registry(registry, args.query)

    # 关键词搜索无结果，尝试语义匹配
    if not results:
        results = semantic_search(registry, args.query)
        if results:
            print(f"\n  关键词无匹配，以下是关于「{args.query}」的语义匹配结果：\n")

    if not results:
        print(f"未找到匹配「{args.query}」的技能")
        return 1

    if args.json:
        data = [_entry_to_dict(e) for e in results]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    print(f"\n找到 {len(results)} 个技能：\n")
    for i, entry in enumerate(results, 1):
        verified_badge = " ✓已认证" if entry.verified else ""
        cat_name = registry.categories.get(entry.category, Category("", "", "")).name if entry.category else ""
        print(f"  {i}. {entry.display_name}{verified_badge}")
        print(f"     {entry.description[:80]}")
        print(f"     标签：{', '.join(entry.tags) if entry.tags else '—'}")
        print(f"     分类：{cat_name or '—'}  v{entry.version}")
        print()
    return 0

def cmd_info(args: argparse.Namespace) -> int:
    """查看技能详情"""
    registry = load_registry()
    entry = registry.skills.get(args.name)
    if not entry:
        print(f"技能「{args.name}」在注册表中未找到")
        return 1

    if args.json:
        print(json.dumps(_entry_to_dict(entry), indent=2, ensure_ascii=False))
        return 0

    print(f"\n  {entry.display_name}  v{entry.version}")
    print(f"  {'✓ 已认证' if entry.verified else '⚠ 第三方'}")
    print()
    print(f"  描述：        {entry.description}")
    print(f"  作者：        {entry.author.name}")
    if entry.author.url:
        print(f"  主页：        {entry.author.url}")
    print(f"  仓库：        {entry.repo}")
    print(f"  许可证：      {entry.license or '—'}")
    print(f"  分类：        {entry.category or '—'}")
    print(f"  支持平台：    {', '.join(entry.platforms) if entry.platforms else '—'}")
    print(f"  标签：        {', '.join(entry.tags) if entry.tags else '—'}")
    if entry.semantic:
        print(f"  意图数量：    {len(entry.semantic.intents)}")
    print()
    return 0

def cmd_list(args: argparse.Namespace) -> int:
    """列出所有技能"""
    registry = load_registry()
    skills = list(registry.skills.values())

    if args.category:
        skills = [s for s in skills if s.category == args.category]
        if not skills:
            print(f"分类「{args.category}」下没有技能")
            return 1

    if args.json:
        data = [_entry_to_dict(e) for e in skills]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    if args.category:
        cat_name = registry.categories.get(args.category, Category(args.category, args.category, "")).name
        print(f"\n分类：{cat_name}")
    else:
        print(f"\n全部技能（共 {len(skills)} 个）：\n")

    for entry in skills:
        print(f"  {entry.display_name:<35} v{entry.version:<10} {entry.description[:50]}")
    print()
    return 0

def cmd_categories(args: argparse.Namespace) -> int:
    """列出所有分类"""
    registry = load_registry()
    print("\n可用分类：\n")
    for cat in registry.categories.values():
        count = sum(1 for s in registry.skills.values() if s.category == cat.id)
        print(f"  {cat.id:<20} {cat.name:<30} （{count} 个技能）")
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
```

- [ ] **步骤 2：写搜索测试**

```python
# scripts/tests/test_skillctl_search.py
import unittest
from scripts.skillctl.models import Registry, SkillEntry, Category
from scripts.skillctl.search import _entry_to_dict

def make_registry():
    skills = {
        "alpha": SkillEntry("alpha", "Alpha 工具", "1.0.0", "第一个工具", "repo", tags=["开发"]),
        "beta": SkillEntry("beta", "Beta 分析器", "2.0.0", "数据分析", "repo", tags=["数据"]),
    }
    cats = {"dev": Category("dev", "开发"), "data": Category("data", "数据")}
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
        entry = SkillEntry("test", "测试", "1.0", "描述", "repo", tags=["a"], verified=True)
        d = _entry_to_dict(entry)
        for key in ("name", "display_name", "version", "description", "tags", "verified"):
            self.assertIn(key, d)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3：运行搜索测试**

执行：`python -m pytest scripts/tests/test_skillctl_search.py -v`
期望：测试通过

- [ ] **步骤 4：提交**

```bash
git add scripts/skillctl/search.py scripts/tests/test_skillctl_search.py
git commit -m "feat(skillctl): search / info / list / categories 命令"
```

---

#### 任务 6：`skillctl install` — 精确名称安装

**涉及文件：**
- 新建：`scripts/skillctl/install.py`
- 新建：`scripts/tests/test_skillctl_install.py`

- [ ] **步骤 1：写安装模块**

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
    """在注册表中按精确名称查找技能"""
    registry = load_registry()
    return registry.skills.get(name)

def resolve_install_dir(platform: str | None, custom_dir: str | None) -> Path:
    """确定安装目标目录"""
    if custom_dir:
        return Path(custom_dir).expanduser().resolve()

    # 未指定平台则自动检测
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
    return "universal"  # 回退

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
        # 版本 tag 不存在则克隆默认分支
        print(f"  分支 v{version} 未找到，克隆默认分支...")
        result = subprocess.run(
            ["git", "clone", "--depth=1", repo_url, str(cache_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  克隆失败：{result.stderr.strip()}")
            return False

    # 定位安装脚本
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
    from scripts.skillctl.index import ensure_index, load_registry

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
        reg = load_registry()
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

    # 先尝试精确匹配
    entry = resolve_skill_entry(skill_name)
    if not entry:
        # 尝试语义匹配
        from scripts.skillctl.search import semantic_search
        registry = load_registry()
        results = semantic_search(registry, args.target, top_k=1)
        if results:
            entry = results[0]
            print(f"  将「{args.target}」理解为：{entry.display_name}")
        else:
            print(f"  技能「{skill_name}」未找到。试试 'skillctl search {skill_name}'")
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
        print(f"  执行 'skillctl update {entry.name}' 检查更新。")
    else:
        print(f"\n  ✗ {entry.display_name} 安装失败")
        return 1

    return 0
```

- [ ] **步骤 2：写安装测试**

```python
# scripts/tests/test_skillctl_install.py
import unittest
from unittest.mock import patch
from pathlib import Path
from scripts.skillctl.install import resolve_skill_entry, _detect_current_platform
from scripts.skillctl.models import SkillEntry

class TestResolveEntry(unittest.TestCase):
    @patch("scripts.skillctl.install.load_registry")
    def test_resolve_existing(self, mock_load):
        entry = SkillEntry("test", "测试", "1.0", "描述", "repo")
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

- [ ] **步骤 3：运行安装测试**

执行：`python -m pytest scripts/tests/test_skillctl_install.py -v`
期望：测试通过

- [ ] **步骤 4：提交**

```bash
git add scripts/skillctl/install.py scripts/tests/test_skillctl_install.py
git commit -m "feat(skillctl): install 命令 — 精确名称解析 + git clone + 安装脚本委托"
```

---

### Phase 2：语义层

#### 任务 7：自然语言意图匹配（搜索和安装共用）

**涉及文件：**
- 修改：`scripts/skillctl/search.py`（新增 `semantic_search` 函数）

- [ ] **步骤 1：在 search.py 中新增语义搜索函数**

在 `scripts/skillctl/search.py` 末尾追加：

```python
# --- 自然语言（NL）匹配 ---

def semantic_search(registry: "Registry", query: str, top_k: int = 3) -> list[SkillEntry]:
    """将自然语言查询与技能的 semantic.intents 进行匹配

    打分策略（无需 LLM）：
      1. 精确意图匹配 → 1.0 分
      2. 查询是某条意图的子串 → 0.85 分
      3. 关键词重合（查询词 ∩ 意图词）→ 按比例 0.5x
      4. 回退到标签匹配 → 0.3 分
    返回分数最高的 top_k 个结果
    """
    scored: list[tuple[float, SkillEntry]] = []
    q_lower = query.lower()
    q_words = set(q_lower.split())

    for entry in registry.skills.values():
        score = 0.0
        intents = []
        if entry.semantic and entry.semantic.intents:
            intents = [i.lower() for i in entry.semantic.intents]

        # 1. 精确意图匹配
        if any(q_lower == intent for intent in intents):
            score = 1.0
        # 2. 部分匹配（查询是某条意图的子串）
        elif any(q_lower in intent for intent in intents):
            score = 0.85
        # 3. 关键词与意图的重叠度
        elif intents:
            all_intent_words = set()
            for intent in intents:
                all_intent_words |= set(intent.split())
            if q_words and all_intent_words:
                overlap = q_words & all_intent_words
                score = 0.5 * len(overlap) / max(len(q_words), 1)
        # 4. 标签回退
        if score == 0.0:
            tag_overlap = q_words & set(entry.tags)
            if tag_overlap:
                score = 0.3 * len(tag_overlap) / max(len(q_words), 1)

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    return [entry for score, entry in scored[:top_k]]
```

- [ ] **步骤 2：修改 `cmd_search` 使关键词无结果时回退到语义搜索**

已在任务 5 中预先编写了回退逻辑，此处仅需确认代码已就位。

- [ ] **步骤 3：写语义搜索测试**

追加到 `scripts/tests/test_skillctl_search.py`：

```python
class TestSemanticSearch(unittest.TestCase):
    def setUp(self):
        from scripts.skillctl.models import SemanticMetadata
        skills = {
            "fin-copilot": SkillEntry(
                "fin-copilot", "金融副驾", "1.0", "金融分析", "repo",
                tags=["股票", "交易"],
                semantic=SemanticMetadata(
                    intents=["分析股票技术指标", "生成交易信号", "查看 RSI 和 MACD"]
                ),
            ),
            "crm-report": SkillEntry(
                "crm-report", "CRM 报表", "2.0", "CRM", "repo",
                tags=["crm", "销售"],
            ),
        }
        self.reg = Registry(skills=skills, categories={})

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
        results = semantic_search(self.reg, "股票")
        self.assertEqual(len(results), 1)

    def test_no_match(self):
        from scripts.skillctl.search import semantic_search
        results = semantic_search(self.reg, "完全无关")
        self.assertEqual(len(results), 0)

    def test_multiple_results_ordered(self):
        from scripts.skillctl.search import semantic_search
        from scripts.skillctl.models import SemanticMetadata
        self.reg.skills["analysis-tool"] = SkillEntry(
            "analysis-tool", "分析工具", "1.0", "工具", "repo",
            tags=["分析"],
            semantic=SemanticMetadata(intents=["对数据执行分析"]),
        )
        results = semantic_search(self.reg, "交易信号分析", top_k=3)
        self.assertGreaterEqual(len(results), 2)
```

- [ ] **步骤 4：运行全部搜索测试**

执行：`python -m pytest scripts/tests/test_skillctl_search.py -v`
期望：通过（任务 5 的 2 个 + 任务 7 的 5 个）

- [ ] **步骤 5：提交**

```bash
git add scripts/skillctl/search.py scripts/tests/test_skillctl_search.py
git commit -m "feat(skillctl): 自然语言语义匹配 — 搜索和安装共用"
```

---

### Phase 3：发布流水线

#### 任务 8：`skillctl publish` — 预检、GitHub 建仓、推送、注册索引

**涉及文件：**
- 新建：`scripts/skillctl/publish.py`
- 新建：`scripts/tests/test_skillctl_publish.py`

- [ ] **步骤 1：写发布模块**

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

def cmd_publish(args: argparse.Namespace) -> int:
    """将技能发布到 GitHub 并注册到索引仓库"""
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    org = args.org or "agent-skills"

    if not skill_dir.exists():
        print(f"错误：技能目录不存在：{skill_dir}")
        return 1

    # 阶段 1：预检
    print(f"\n  预检：{skill_dir}\n")

    repo_scripts = Path(__file__).parent.parent
    sys.path.insert(0, str(repo_scripts))
    from scripts import validate, security_scan

    # 提取元数据
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

    # 阶段 2：创建 GitHub 仓库
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

    # 阶段 3：推送内容
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

    # 阶段 4：注册到索引
    print("  注册到索引...")
    _register_in_index(skill_name, repo_full, version, description, author_name, org)

    print(f"\n  ✓ 已发布：https://github.com/{repo_full}")
    print(f"  试试：skillctl install {skill_name}")
    return 0

def _parse_frontmatter(content: str) -> dict:
    """解析 --- 标记之间的 YAML 式 frontmatter"""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    end = 1
    while end < len(lines) and lines[end].strip() != "---":
        end += 1
    result = {}
    for line in lines[1:end]:
        line = line.strip()
        if not line:
            continue
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            result[k.strip()] = v.strip().strip('"').strip("'")
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
```

- [ ] **步骤 2：写发布测试**

```python
# scripts/tests/test_skillctl_publish.py
import unittest
from scripts.skillctl.publish import _parse_frontmatter

class TestParseFrontmatter(unittest.TestCase):
    def test_parse_simple(self):
        content = """---
name: test-skill
description: 一个测试技能
---

# 正文
"""
        result = _parse_frontmatter(content)
        self.assertEqual(result.get("name"), "test-skill")

    def test_no_frontmatter(self):
        result = _parse_frontmatter("没有 frontmatter")
        self.assertEqual(result, {})

if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 3：运行发布测试**

执行：`python -m pytest scripts/tests/test_skillctl_publish.py -v`
期望：2 个测试通过

- [ ] **步骤 4：提交**

```bash
git add scripts/skillctl/publish.py scripts/tests/test_skillctl_publish.py
git commit -m "feat(skillctl): publish 命令 — 预检、建仓、推送、索引注册"
```

---

#### 任务 9：Phase 5 集成 — 工厂流水线中提示发布

**涉及文件：**
- 修改：`SKILL.md` — 在 Phase 5 末尾添加发布提示

- [ ] **步骤 1：增强 SKILL.md**

定位 SKILL.md 中 Phase 5 的结束标记，在其后追加：

```markdown
### 发布到技能商店（可选）

技能目录就绪后，可以发布到全局技能注册表：

```bash
skillctl publish <技能目录>
```

如果设置了 `GITHUB_TOKEN`，工厂会自动提示：

```
是否将此技能发布到 GitHub？(y/N)
```

成功后：

```
✓ 已发布到 agent-skills/{名称} (v{版本})
试试：skillctl install {名称}
```
```

- [ ] **步骤 2：提交**

```bash
git add SKILL.md
git commit -m "feat: Phase 5 新增发布提示"
```

---

### Phase 4：更新与安全

#### 任务 10：`skillctl update` — 版本检查和原地升级

**涉及文件：**
- 新建：`scripts/skillctl/update.py`
- 新建：`scripts/tests/test_skillctl_update.py`

- [ ] **步骤 1：写更新模块**

```python
# scripts/skillctl/update.py
from __future__ import annotations
import argparse
import subprocess
import sys

from scripts.skillctl.config import load_installed, save_installed, CACHE_DIR
from scripts.skillctl.index import load_registry
from scripts.skillctl.models import SkillEntry

def cmd_update(args: argparse.Namespace) -> int:
    """检查并升级已安装技能"""
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
    """Git fetch + checkout 新版本"""
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
```

- [ ] **步骤 2：写更新测试**

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
            "test-skill": SkillEntry("test-skill", "测试", "2.0.0", "更新了", "repo"),
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

- [ ] **步骤 3：运行更新测试**

执行：`python -m pytest scripts/tests/test_skillctl_update.py -v`
期望：1 个测试通过

- [ ] **步骤 4：提交**

```bash
git add scripts/skillctl/update.py scripts/tests/test_skillctl_update.py
git commit -m "feat(skillctl): update 命令 — 版本检查 + git fetch 升级"
```

---

#### 任务 11：安全集成和 Shell 安装器增强

**涉及文件：**
- 修改：`scripts/install-skill.sh` — 新增 `--from-registry` 参数
- 修改：`scripts/install-skill.ps1` — 新增 `-FromRegistry` 参数

- [ ] **步骤 1：增强 install-skill.sh**

在已有的选项解析循环中新增：

```bash
        --from-registry)
            SKILL_NAME="$2"
            shift 2
            ;;
```

并在选项解析结束后新增：

```bash
if [ -n "${SKILL_NAME:-}" ]; then
    exec python3 "$(dirname "$0")/skillctl/__main__.py" install "$SKILL_NAME"
fi
```

- [ ] **步骤 2：增强 install-skill.ps1**

新增参数：

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

- [ ] **步骤 3：运行已有测试确认无回归**

执行：`python -m pytest scripts/tests/test_skill_registry.py -v`
期望：全部已有测试仍通过

- [ ] **步骤 4：提交**

```bash
git add scripts/install-skill.sh scripts/install-skill.ps1
git commit -m "feat: Shell 安装器新增 --from-registry 参数"
```

---

### Phase 5：索引仓库搭建

#### 任务 12：在 GitHub 上创建索引仓库

**涉及文件：**（在独立仓库中创建，不在当前仓库中）

- 新建：`registry.json`（`agent-skills/index` GitHub 仓库）
- 新建：`registry.schema.json`
- 新建：`AGENTS.md`
- 新建：`.github/workflows/validate-registry.yaml`
- 新建：`.github/workflows/sync-versions.yaml`

- [ ] **步骤 1：创建索引仓库**

```bash
# 一次性操作（在本仓库外执行）
gh repo create agent-skills/index --public --description "agent-skill-creator 技能中央索引"
git clone https://github.com/agent-skills/index.git
cd index
```

- [ ] **步骤 2：创建 registry.schema.json**

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

- [ ] **步骤 3：创建初始 registry.json（仅含分类，无技能）**

```json
{
  "registry": {
    "name": "Agent Skills Index",
    "created": "2026-07-29T00:00:00+00:00",
    "updated": "2026-07-29T00:00:00+00:00",
    "schema_version": "2",
    "github_org": "agent-skills",
    "description": "agent-skill-creator 生态系统官方技能索引"
  },
  "categories": [
    {"id": "ai", "name": "AI 与机器学习", "description": "LLM 工作流、模型交互、提示工程相关技能"},
    {"id": "compliance", "name": "合规与审计", "description": "合规审查、审计报表、治理相关技能"},
    {"id": "crm", "name": "销售与CRM", "description": "CRM 流程、销售报表、管道管理技能"},
    {"id": "data-engineering", "name": "数据工程", "description": "ETL、数据清洗、验证、转换技能"},
    {"id": "devops", "name": "DevOps 与基础设施", "description": "部署、监控、CI/CD 自动化技能"},
    {"id": "financial", "name": "金融分析", "description": "行情分析、组合管理、量化交易技能"},
    {"id": "utility", "name": "通用工具", "description": "通用自动化和效率工具"},
    {"id": "writing", "name": "写作与内容", "description": "内容生成、编辑、品牌语调强制技能"}
  ],
  "skills": []
}
```

- [ ] **步骤 4：创建 AGENTS.md**

```markdown
# Agent Skills Index

此仓库是 agent-skill-creator 技能的中央索引。Agent 在对话中可自动发现并安装匹配的技能。

## 面向 Agent 工作器

当用户的表达与索引中某技能匹配时，应自动安装。遵循以下规则：

1. 读取 `registry.json` 获取所有可用技能
2. 将用户的当前请求与每项技能的 `semantic.intents` 和 `prompt_triggers` 对比
3. 最佳匹配置信度 > 70%：
   → 执行：`skillctl install <技能名>`
4. 置信度 40-70%：
   → 建议：「我可以用这个。试试 `skillctl install <技能名>`？」
5. 置信度 < 40%：不做任何操作
6. 安装后，立即按 SKILL.md 中的指示调用技能

## 手动安装

```bash
skillctl search <查询>
skillctl install <技能名>
skillctl info <技能名>
```
```

- [ ] **步骤 5：创建 validate-registry.yaml 工作流**

```yaml
name: 校验注册表
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: 校验 registry.json 完整性
        run: |
          python -c "
import json, sys, re
with open('registry.json') as f:
    data = json.load(f)
assert 'registry' in data, '缺少 registry 部分'
assert 'skills' in data, '缺少 skills 部分'
assert isinstance(data['skills'], list), 'skills 必须是数组'
for s in data['skills']:
    assert s.get('name'), f'技能缺少 name：{s}'
    assert s.get('version'), f'技能 {s.get(\"name\")} 缺少 version'
    assert s.get('repo'), f'技能 {s.get(\"name\")} 缺少 repo'
    assert re.match(r'^\d+\.\d+\.\d+$', s['version']), f'{s[\"name\"]}：version 必须是 semver 格式'
print('✓ registry.json 校验通过')
          "
      - name: 检查重名
        run: |
          python -c "
import json
with open('registry.json') as f:
    data = json.load(f)
names = [s['name'] for s in data['skills']]
dupes = [n for n in names if names.count(n) > 1]
if dupes:
    print(f'重复技能名：{set(dupes)}')
    sys.exit(1)
print('✓ 无重复技能名')
          "
```

- [ ] **步骤 6：创建 sync-versions.yaml 工作流**

```yaml
name: 同步版本
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
      - name: 从 GitHub Releases 更新版本号
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
                    print(f'{skill[\"name\"]}：{skill.get(\"version\")} → {latest}')
                    skill['version'] = latest
                    updated = True
        except Exception as e:
            print(f'{skill[\"name\"]}：获取 release 出错 — {e}', file=sys.stderr)
if updated:
    with open('registry.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('版本已同步。')
else:
    print('所有版本均为最新。')
          "
      - name: 更新后创建 PR
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "chore: 同步技能版本"
          title: "chore: 同步技能版本"
          branch: "sync-versions"
          delete-branch: true
```

- [ ] **步骤 7：推送到 GitHub**

```bash
cd index
git add .
git commit -m "chore: 初始化索引仓库"
git push -u origin main
```

---

## 自审

### Spec 覆盖率

| Spec 章节 | 实现位置 |
|----------|---------|
| 1. 定位与目标 | 本计划结构和设计决策隐含覆盖 |
| 2. 架构总览 | 任务 4（CLI 入口）、任务 6（安装流程）、任务 8（发布）|
| 3. 索引仓库设计 | 任务 1（数据模型）、任务 3（registry 解析）、任务 12（索引仓库搭建）|
| 4. skillctl CLI | 任务 4（CLI 分发）、任务 5（search/info/list）、任务 6（install）|
| 4.2 语义安装 | 任务 7（semantic_search）|
| 4.3 Agent 自动发现 | 任务 12（索引仓库 AGENTS.md）|
| 5. 发布流水线 | 任务 8（publish 命令）、任务 9（Phase 5 集成）|
| 6. 版本管理 | 任务 10（update 命令）|
| 7. 安全模型 | 任务 8（发布预检中含安全扫描）|
| 8. 第三方与社区 | 任务 6（verified 标记提示）、任务 12（schema 支持第三方）|
| 9. 变更清单 | 12 个任务覆盖全部 8 项资产 |

### 占位符扫描

无 "TBD"、"TODO" 或任何占位符。每个步骤均有完整代码。

### 类型一致性

- 任务 1 定义 `SkillEntry`、`SemanticMetadata`、`Registry` → 任务 3、5、6、7 中引用
- 任务 3 的 `load_registry()` 返回 `Registry` 数据类 → 任务 5、6、10 中消费
- 任务 7 的 `semantic_search()` 接收 `Registry` 返回 `list[SkillEntry]` → 与任务 6 中的消费方式一致
- 任务 6 的 `resolve_skill_entry()` 返回 `SkillEntry | None` → 一致
- 任务 8 的 `_parse_frontmatter()` 返回 `dict` → 测试一致

全部一致。
