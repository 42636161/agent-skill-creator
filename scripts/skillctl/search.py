from __future__ import annotations
import argparse
import json
import sys

from scripts.skillctl.index import load_registry, search_registry
from scripts.skillctl.models import Registry, SkillEntry, Category

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

def semantic_search(registry: Registry, query: str, top_k: int = 3) -> list[SkillEntry]:
    """将自然语言查询与技能的 semantic.intents 进行匹配"""
    scored: list[tuple[float, SkillEntry]] = []
    q_lower = query.lower()
    q_words = set(q_lower.split())

    for entry in registry.skills.values():
        score = 0.0
        intents = []
        if entry.semantic and entry.semantic.intents:
            intents = [i.lower() for i in entry.semantic.intents]

        if any(q_lower == intent for intent in intents):
            score = 1.0
        elif any(q_lower in intent for intent in intents):
            score = 0.85
        elif intents:
            all_intent_words = set()
            for intent in intents:
                all_intent_words |= set(intent.split())
            if q_words and all_intent_words:
                overlap = q_words & all_intent_words
                score = 0.5 * len(overlap) / max(len(q_words), 1)
        if score == 0.0:
            tag_overlap = q_words & set(entry.tags)
            if tag_overlap:
                score = 0.3 * len(tag_overlap) / max(len(q_words), 1)

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    return [entry for score, entry in scored[:top_k]]
