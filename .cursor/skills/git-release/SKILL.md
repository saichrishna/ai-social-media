---
name: git-release
description: Local git inspection and optional commit after explicit user approval. Use for status, diff, and log review. Never push or run destructive git without a separate explicit approval.
---

# Git / release

Local Git only. No remote MCP.

## Always allowed

- `git status`
- `git diff` / `git diff --staged`
- `git log` (read-only)

## Commit (explicit approval required)

Commit only when the user clearly asks to commit (this turn). Then:

1. Inspect status and diff.
2. Stage only task-related files.
3. Confirm `.env`, `agent-models.env`, credentials, and generated media are **not** staged.
4. Write a concise message focused on why.
5. Commit. Do not amend unless the user asks and amend safety rules are met.
6. Show `git status` after the commit.

Never skip hooks.

## Never without a separate explicit instruction

- `git push` / `git push --force`
- `git reset --hard`
- `git clean`
- branch deletion
- destructive filesystem deletes

## Secrets

- Do not read or print `.env`.
- If `.env` appears in status as untracked, it must stay untracked.
