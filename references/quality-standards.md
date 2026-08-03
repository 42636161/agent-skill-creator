# Quality Standards for Generated Skills

**Loaded: always.** Core quality patterns. Detailed checklists are in `references/pipeline-phases.md`.

## Code Quality

### Always
- Complete, functional code with no TODOs, no `pass`, no placeholder functions
- Detailed docstrings (Google or NumPy style) and type hints on all public functions
- Robust error handling: try/except for file I/O and network calls, meaningful error messages
- Real content in references (not "see docs" or "TBD")
- Configs with real values, not placeholders

### Never
- Placeholder code or empty function bodies
- `api_key: YOUR_KEY_HERE` without env var instructions
- SKILL.md over 500 lines (merge into `references/guide.md` if needed)
- Platform-specific hacks or hardcoded paths
- Fabricated data or guessed API responses (mark with `# TODO: verify` if uncertain)

## Output Quality

- Report output starts with executive summary, not a raw data table.
- Pipeline stdout is human-readable by default; `--json` flag for machine output.
- Empty/missing values are explicitly marked (null, N/A, 0) — never silently omitted.
- Multi-file outputs each have a documented purpose.

## Testing Strategy

- Eval golden cases must include boundary values: zero, negative, missing, extreme.
- `run_evals.py --rollout` must pass on all golden cases before delivery.
- Split golden cases: `train` for development, `test` for release-only scoring.
- Regression gate: `--promote` captures baseline; subsequent runs must match or exceed.

## Dependency Management

- Declare all dependencies: Python version, required packages.
- Use stdlib when possible (csv, sqlite3, pathlib, json).
- External libraries: pin minimum versions, document why they're needed.
- No system-level dependencies unless unavoidable.

## Security Baseline

- `security_scan.py` must pass with 0 high-severity findings before delivery.
- No hardcoded API keys, tokens, or secrets in any file.
- `.env` files: never commit. Document in `.env.example` with placeholder values.
- Salary/personal data: never log to stdout. Output files carry data protection warning.
