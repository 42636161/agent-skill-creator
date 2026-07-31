# Contributing

Thanks for your interest in improving **agent-skill-creator**. This skill
generates cross-platform agent skills, so changes need to keep the generator
correct and its tests green.

## Workflow

1. Fork the repository and create a feature branch.
2. Make your changes.
3. Add or update tests under `scripts/tests/`.
4. Run the checks below — they must pass.
5. Open a pull request describing what changed and why.

## Local checks

The tooling is stdlib-only Python; tests run with `pytest`.

```bash
# Run the full test suite (must be green)
uv run pytest scripts/tests/

# Validate a skill's SKILL.md against the spec
python3 scripts/validate.py <skill-dir>

# Verify a skill's script pipeline (compiles, deps declared)
python3 scripts/check_pipeline.py <skill-dir>

# Security scan
python3 scripts/security_scan.py <skill-dir>
```

## Conventions

- **Commits:** conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`,
  `test:`, `chore:`).
- **Style:** PEP 8, type annotations on function signatures, `ruff` clean.
- **Unified install:** generated skills carry no installer. The `skillctl` CLI
  handles installation from `scripts/platforms.py`, so platform additions only
  need to update that registry, not a shell installer.
- **Single source of truth:** SKILL.md parsing lives in `scripts/skill_document.py`
  and the install-target list in `scripts/platforms.py` — extend those rather than
  re-implementing parsing or hardcoding platform paths.

## Adding a new platform

The most common contribution. A platform addition touches a fixed set of
files — change them together or CI's parity tests will catch the drift:

1. **`scripts/platforms.py`** — add the platform tuple (name, user-level
   install path, project-level install path, detection directory). This is
   the single source of truth `skillctl` reads at install time.
2. **Docs** — add the platform to the tier table in `SKILL.md` and
   `references/cross-platform-guide.md`. If the platform needs a format
   adapter (not native SKILL.md), document the transformation in the Tier 2
   section.
3. **Platform count** — the number of supported platforms is stated in
   `README.md`, `SKILL.md`, and `references/cross-platform-guide.md`. Bump
   it in **all three** in the same PR (and remind a maintainer to update the
   GitHub repo description).

Then verify:

```bash
uv run pytest scripts/tests/test_platforms.py
```

`test_platforms.py` verifies the registry is well-formed, so a partial addition
fails loudly.

## A note on eval specs

Generated skills bundle `run_evals.py` (from `scripts/run_evals_template.py`),
which executes spec-defined command checks via the shell, compares rollout
output against promoted baselines (regression gate), holds out `"split": "test"`
cases from optimization, and — with `--judge` — grades `llm-judge` criteria via
a judge pinned in the spec (with a known-bad canary that must fail). Skills also
bundle `evolve.py` (from `scripts/evolve_template.py`). Eval specs are trusted
input — only run evals from specs you or your team wrote.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
