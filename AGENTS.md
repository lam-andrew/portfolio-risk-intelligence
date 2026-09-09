# Orbit Agent Instructions

These instructions apply to all work in this repository. The user’s explicit
request takes precedence when it conflicts with this file; otherwise follow this
file and the referenced project standards.

## Before changing anything

- Read `CLAUDE.md`, `CONTRIBUTING.md`, and `README.md`.
- Read the relevant living documentation under `docs/` and any applicable ADRs.
- Check `git status`, the current branch, recent commits, and existing user changes.
- Treat the GitHub Issues and Project board as the authoritative story and status
  records; do not invent story scope or silently change sprint assignment.

## Git and review workflow

- Never commit directly to `main` or push directly to `main`.
- Create a focused feature, fix, docs, or chore branch using the `codex/` prefix.
- Keep commits small and related to one logical change or story.
- Push the branch and open a pull request before merging.
- Do not merge until the PR diff has been reviewed and required CI/security checks
  pass. Merge through GitHub, not with a local fast-forward into `main`.
- Link the relevant issue or story in the PR and describe tests and documentation
  changes in the PR body.

## Story completion and scope

- Do not close an issue or mark a story Done solely because code exists.
- Verify acceptance criteria, Definition of Done tasks, automated tests, and any
  required User Acceptance Testing before claiming completion.
- Protect the core Risk & Exposure engine. Put new ideas in the backlog unless the
  user explicitly changes the current scope or sprint plan.
- Report work completed early using its actual date; do not rewrite sprint history.

## Quality and documentation

- New backend logic requires pytest coverage; frontend behavior requires frontend
  tests where appropriate.
- Run proportionate lint, type-check, test, build, and security checks before the
  PR. Report exactly what ran and any limitations.
- Update living documentation when behavior, requirements, testing evidence,
  architecture, or user workflow changes.
- Create or update an ADR for an architectural, data-flow, security, deployment,
  API-contract, or other long-term design decision. Do not create ADR noise for
  small reversible edits.
- Never commit secrets, credentials, private tokens, or cached external data.

## Communication

- State assumptions and blockers clearly.
- Do not claim a change is merged, tested, deployed, or accepted without evidence.
- If a requested action would materially conflict with these standards, explain the
  conflict before proceeding.
