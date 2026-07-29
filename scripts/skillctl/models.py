from __future__ import annotations
from dataclasses import dataclass, field
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
