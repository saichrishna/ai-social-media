# Agent-led development

This repository has two different agent systems. Do not mix them.

## Cursor development agents (this file)

These agents write and review **software** in this repo. They are coordinated by the **orchestrator** (the primary chat agent).

| Role | Kind | Writes code? | Git writes? |
| --- | --- | --- | --- |
| Orchestrator | Parent coordinator | No (delegates) | No |
| Architect | `.cursor/agents/architect.md` | No (read-only) | No |
| Developer | `.cursor/agents/developer.md` | Yes, after an approved plan | No |
| Debugger | `.cursor/agents/debugger.md` | Minimal diagnostic fixes only | No |
| Code reviewer | `.cursor/agents/code-reviewer.md` | No (read-only) | No |
| Git/release | `.cursor/agents/git-release.md` | No application code | Status/diff/log always; **commit only with explicit user approval** |

Detailed checklists: `.cursor/skills/<role>/SKILL.md`.

## Runtime content agents (do not treat as Cursor agents)

`agents/content_strategist.py`, `agents/prompt_engineer.py`, `agents/content_generator.py`, and `agents/content_reviewer.py` generate **social media content** via Ollama at runtime. They are product code. Do not replace, rename, or “upgrade” them into Cursor development agents.

## Workflow

1. Requirement
2. Repository inspection
3. Architecture / plan (architect)
4. Implementation (developer)
5. Tests (developer)
6. Debugging if required (debugger)
7. Code review (code reviewer)
8. Git diff review (git/release)
9. Commit **only** after the user explicitly approves

## Orchestrator rules

- Delegate to specialists. Do not implement, review, and commit in one pass.
- Inspect relevant files before any change. Never blindly edit existing code.
- Preserve existing architecture unless the approved plan documents why it must change.
- Keep changes focused and minimal.
- Never push, force-push, reset, or clean without explicit user approval.
- Never expose or commit secrets or `.env`.
- Never inspect `.env` contents.

## Models (local-first, configurable)

Custom Cursor agents use `model: inherit`. They must **not** hardcode Ollama or other model names.

Copy `.cursor/config/agent-models.env.example` to `.cursor/config/agent-models.env` (gitignored) to set local role-to-model mappings. Application Ollama settings stay in `.env` / `config.py` (`OLLAMA_HOST`, `OLLAMA_MODEL`) and are for **runtime content generation**, not Cursor agents.

## MCP

Project MCP is empty (`.cursor/mcp.json`). Use local filesystem, terminal, and local Git. Do not add GitHub or other remote MCP servers unless the user explicitly asks.
