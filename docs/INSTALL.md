# Installation Guide

`agent-skill-creator` and the skills it generates install through the unified
`skillctl` CLI. Install the CLI once, then use the same commands on every
platform.

---

## Install skillctl

**macOS / Linux / WSL:**

```bash
curl -fsSL https://raw.githubusercontent.com/42636161/skillhub/main/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/42636161/skillhub/main/install.ps1 | iex
```

Verify:

```bash
skillctl doctor
```

## Install agent-skill-creator

From the registry:

```bash
skillctl install agent-skill-creator
```

The factory is copied into every detected platform's skills path, so you can
invoke `/agent-skill-creator` from Claude Code, Codex CLI, Gemini CLI, Cursor,
Copilot, and the other supported tools.

**Manual fallback (clone):**

```bash
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.agents/skills/agent-skill-creator
```

For per-tool placement, see [Global install](#global-install-each-tools-native-path) below.

---

## All Platforms

17 platforms supported. Same skill, same invocation, same results everywhere.

### How it works

Every generated skill ships **SKILL.md**, the activation mechanism on every
platform. `skillctl` reads the canonical platform registry
(`scripts/platforms.py`), detects the current tool, generates format adapters
for Tier 2 platforms (Cursor `.mdc`, Windsurf `.md` rules, Trae `.md`, Junie
`guidelines.md`), and copies the skill to the right path.

| Tier | Platforms | What happens |
|------|-----------|-------------|
| **Tier 1 — Native SKILL.md** | Claude Code, Copilot, Codex CLI, Gemini CLI, Kiro, Cline, Roo Code, Kilo Code, Goose, OpenCode, Factory Droid, Antigravity | Reads SKILL.md directly |
| **Tier 2 — Auto-adapted** | Cursor, Windsurf, Trae, Junie | `skillctl` converts SKILL.md to native format (.mdc, .md rules, guidelines) |
| **Tier 3 — Manual** | Zed, Augment, Aider, Continue.dev | Copy skill body into tool's config file |

### Global install (each tool's native path)

Use skillctl:

```bash
skillctl install agent-skill-creator            # auto-detect platform
skillctl install agent-skill-creator --all      # every detected platform
```

Manual fallback — clone directly into the tool's path:

```bash
# Claude Code
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.claude/skills/agent-skill-creator

# GitHub Copilot
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.copilot/skills/agent-skill-creator

# Gemini CLI
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.gemini/skills/agent-skill-creator

# Kiro
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.kiro/skills/agent-skill-creator

# Cline
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.cline/skills/agent-skill-creator

# Roo Code
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.roo/skills/agent-skill-creator

# Kilo Code
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.kilocode/skills/agent-skill-creator

# Factory Droid
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.factory/skills/agent-skill-creator

# Goose
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.config/goose/skills/agent-skill-creator

# OpenCode
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.config/opencode/skills/agent-skill-creator

# Codex CLI / universal path (read by 7+ tools as fallback)
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/.agents/skills/agent-skill-creator
```

Use each tool's own native path. The universal `~/.agents/skills/` path works
as a fallback for Codex CLI, Gemini CLI, OpenCode, Goose, Cline, Roo Code, and
Kilo Code.

### Per-project install

```bash
# GitHub Copilot
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .github/skills/agent-skill-creator

# Cursor (project only — no global path exists)
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .cursor/skills/agent-skill-creator

# Windsurf
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .windsurf/rules/agent-skill-creator

# Cline
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .clinerules/skills/agent-skill-creator

# Kiro
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .kiro/skills/agent-skill-creator

# Trae
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .trae/rules/agent-skill-creator

# Roo Code
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .roo/skills/agent-skill-creator

# Kilo Code
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .kilocode/skills/agent-skill-creator

# Junie (JetBrains)
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .junie/skills/agent-skill-creator

# Antigravity (note: .agent/ singular, NOT .agents/)
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git .agent/skills/agent-skill-creator
```

### Cursor — global workaround

Cursor has no global skills directory. Clone once and symlink per project:

```bash
# 1. Clone once
git clone https://github.com/FrancyJGLisboa/agent-skill-creator.git ~/agent-skills/agent-skill-creator

# 2. In any project, symlink
mkdir -p .cursor/rules && ln -s ~/agent-skills/agent-skill-creator .cursor/rules/agent-skill-creator
```

Add a shell alias to automate this (`~/.zshrc` or `~/.bashrc`):

```bash
alias install-skills='mkdir -p .cursor/rules && ln -s ~/agent-skills/agent-skill-creator .cursor/rules/agent-skill-creator'
```

Then in any project: `install-skills`. Updates propagate automatically via the
symlink.

---

## Install Generated Skills

Skills produced by the factory install with the same CLI:

```bash
skillctl install <skill-name>                  # Auto-detect platform
skillctl install <skill-name> --platform cursor
skillctl install <skill-name> --all            # Install to every detected tool at once
skillctl update <skill-name>                   # Upgrade later
```

`skillctl` resolves all 17 platform skills paths from the canonical registry
and copies the skill directly.

### Claude Desktop / claude.ai

```bash
python3 scripts/export_utils.py ./agent-skill-creator/ --variant desktop
# Then: Settings > Skills > Upload the generated .zip
```

### Update

```bash
skillctl update agent-skill-creator
```

If you installed by clone, `cd ~/.agents/skills/agent-skill-creator && git pull`
updates in place.

---

## Install Any Skill

Install the CLI once, then use the same commands on every platform:

```bash
# From the registry (GitHub index)
skillctl install sales-report-skill

# Natural-language semantic install
skillctl install "帮我生成每周销售报表"

# To a specific platform only
skillctl install sales-report-skill --platform cursor --project

# Install to every detected platform
skillctl install sales-report-skill --all

# Upgrade / check
skillctl update sales-report-skill
skillctl update --all
```
