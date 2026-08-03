#!/usr/bin/env python3
"""
Master test orchestrator for retail skill performance evaluation.

This script does NOT invoke the agent-skill-creator automatically (the creator
is an agent-internal pipeline, not a CLI). Instead it:
  1. Generates all test data
  2. Prints a step-by-step test protocol for each case
  3. After manual/agent-driven generation, scores all outputs

Usage:
    python3 tests/retail_skills/run_all.py generate     # Step 1: generate test data
    python3 tests/retail_skills/run_all.py protocol     # Step 2: print test protocol
    python3 tests/retail_skills/run_all.py score <dir>  # Step 3: score generated skills
    python3 tests/retail_skills/run_all.py full <dir>   # Generate + protocol + (placeholder for score)
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def cmd_generate():
    """Run the data generator."""
    print("=" * 60)
    print("STEP 1: Generating test data")
    print("=" * 60)
    subprocess.run(["python3", str(SCRIPT_DIR / "generate_data.py")], check=True)


def cmd_protocol():
    """Print the human-readable test protocol for each case."""
    with open(SCRIPT_DIR / "test_spec.json") as f:
        spec = json.load(f)

    print("=" * 60)
    print("STEP 2: Test Protocol — invoke each case with agent-skill-creator")
    print("=" * 60)
    print()

    for case in spec["cases"]:
        cid = case["id"]
        name = case["name"]
        input_type = case["input_type"]
        prompt = case["input_prompt"]
        files = case.get("input_files", [])
        expected_name = case["expected_skill_name"]
        expected_arch = case["expected_architecture"]
        target = case["pipeline_phase_target"]

        print(f"{'─' * 60}")
        print(f"[{cid.upper()}] {name}")
        print(f"  Target phase: {target}")
        print(f"  Expected: {expected_arch} → {expected_name}")
        print()

        if input_type == "file_only":
            abs_files = [str((SCRIPT_DIR / f).resolve()) for f in files]
            print(f"  输入：丢一个文件进去")
            for af in abs_files:
                print(f"    📎 {af}")
            print(f"  说：\"{prompt}\"")
            print()
            print(f"  操作：在 Codex 对话中上传上述文件，然后输入：")
            print(f"    /agent-skill-creator {prompt}")
            print(f"    [+ 上传文件: {abs_files[0]}]")

        elif input_type == "text_only":
            print(f"  输入：纯文字")
            print(f"  操作：在 Codex 对话中输入：")
            print(f"    /agent-skill-creator {prompt}")

        elif input_type == "text_only_minimal":
            print(f"  输入：极简（一个字/词）")
            print(f"  操作：在 Codex 对话中输入：")
            print(f"    /agent-skill-creator {prompt}")
            print(f"  注意：此用例测试 Phase 0 spec ideation，应看到 hypothesis 确认而非直接建 skill")

        elif input_type == "mixed":
            abs_files = [str((SCRIPT_DIR / f).resolve()) for f in files]
            print(f"  输入：文件 + 描述")
            for af in abs_files:
                print(f"    📎 {af}")
            print(f"  说：\"{prompt}\"")
            print()
            print(f"  操作：在 Codex 对话中上传上述文件，然后输入：")
            print(f"    /agent-skill-creator {prompt}")
            if files:
                print(f"    [+ 上传文件: {', '.join(abs_files)}]")

        print()
        print(f"  ⏱ 生成完成后，将 skill 目录保存到：")
        print(f"    outputs/{expected_name}/")

        # Print critical checks as reminders
        critical = case.get("critical_checks", [])
        if critical:
            print()
            print(f"  🔍 生成时重点关注（creator 应自动满足，但检查员需核对）：")
            for cc in critical[:3]:
                print(f"    • {cc}")
            if len(critical) > 3:
                print(f"    • ... (+{len(critical)-3} more, see test_spec.json)")

        print()

    print("=" * 60)
    print("All cases printed. After generating all skills, run:")
    print("  python3 tests/retail_skills/run_all.py score outputs/")
    print("=" * 60)


def cmd_score(outputs_dir: str):
    """Score all generated skills."""
    print("=" * 60)
    print("STEP 3: Scoring generated skills")
    print("=" * 60)
    subprocess.run(
        ["python3", str(SCRIPT_DIR / "score_skill.py"), "--all", outputs_dir],
        check=True
    )


def cmd_full(outputs_dir: str):
    """Run all steps (generate + protocol; score must be done separately)."""
    cmd_generate()
    print("\n")
    cmd_protocol()
    print("\n")
    print("=" * 60)
    print("After generating all skills into the outputs/ directory, run:")
    print(f"  python3 tests/retail_skills/score_skill.py --all {outputs_dir}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 run_all.py generate          # Generate test data")
        print("  python3 run_all.py protocol          # Print test protocol")
        print("  python3 run_all.py score <dir>       # Score generated skills")
        print("  python3 run_all.py full <outputs_dir># Generate + print protocol")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "generate":
        cmd_generate()
    elif cmd == "protocol":
        cmd_protocol()
    elif cmd == "score":
        cmd_score(sys.argv[2] if len(sys.argv) > 2 else "outputs/")
    elif cmd == "full":
        cmd_full(sys.argv[2] if len(sys.argv) > 2 else "outputs/")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
