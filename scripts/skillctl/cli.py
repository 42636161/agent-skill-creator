from __future__ import annotations
import argparse
import sys

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillctl",
        description="Agent 技能 CLI — 发现、安装、发布 Agent 技能",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="搜索技能")
    p_search.add_argument("query", help="搜索关键词或自然语言描述")
    p_search.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    p_install = sub.add_parser("install", help="安装技能")
    p_install.add_argument("target", help="技能名称（可含版本号，如 name@1.0.0）或自然语言描述")
    p_install.add_argument("--dir", help="安装到自定义目录")
    p_install.add_argument("--platform", help="目标平台名称")
    p_install.add_argument("--all", action="store_true", help="安装到全部检测到的平台")

    p_info = sub.add_parser("info", help="查看技能详情")
    p_info.add_argument("name", help="技能名称")
    p_info.add_argument("--json", action="store_true")

    p_list = sub.add_parser("list", help="列出所有可用技能")
    p_list.add_argument("--category", help="按分类过滤")
    p_list.add_argument("--json", action="store_true")

    p_update = sub.add_parser("update", help="更新已安装技能")
    p_update.add_argument("name", nargs="?", help="技能名称（留空则更新全部）")
    p_update.add_argument("--check", action="store_true", help="仅检查更新不执行")

    sub.add_parser("categories", help="列出技能分类")
    sub.add_parser("doctor", help="检查 CLI 和索引仓库健康状态")

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
