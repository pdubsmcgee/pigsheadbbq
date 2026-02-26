# AGENTS.md — General Web Project Template

This file defines guidance for AI coding agents and contributors working in this repository.

## Purpose

Use this template for building and maintaining web applications (frontend, backend, or full-stack) with clear conventions, safe changes, and predictable delivery.

## Core Principles

- Prioritize correctness, readability, and maintainability over cleverness.
- Keep changes small, focused, and easy to review.
- Prefer explicit code and clear naming.
- Preserve backwards compatibility unless a breaking change is explicitly requested.
- Document non-obvious decisions in code comments or docs.

## How to Work

1. Understand the request and constraints before editing.
2. Inspect existing patterns in the codebase and follow them.
3. Propose/implement the smallest viable change.
4. Validate with lint, type checks, tests, and build when available.
5. Summarize what changed, why, and how it was verified.

## Planning and Execution

- For multi-step work, create a short plan and update it as you progress.
- Complete one concern at a time (data model, API, UI, tests, docs).
- Call out assumptions and risks early.

## Coding Standards

- Match established project style (formatter, linter, naming conventions).
- Keep functions/modules cohesive; avoid large monolithic files.
- Avoid dead code and commented-out blocks.
- Never use single-letter variable names except for trivial loop indexes.
- Prefer pure functions and deterministic behavior where practical.

## Web Frontend Guidance

- Build accessible UI by default:
  - Use semantic HTML.
  - Ensure keyboard navigation and visible focus states.
  - Use accessible names/labels for controls.
  - Meet reasonable color contrast.
- Make responsive layouts that work across common screen sizes.
- Minimize layout shift and unnecessary re-renders.
- Handle loading, empty, error, and success states explicitly.
- Keep components small and composable.

## Backend/API Guidance

- Validate all input at the boundary.
- Return consistent error formats and status codes.
- Keep business logic separate from transport/framework glue.
- Use idempotency and retries thoughtfully for external calls.
- Avoid leaking secrets or internal stack details in responses/logs.

## Data and Persistence

- Prefer explicit migrations for schema changes.
- Make data changes backward compatible when possible.
- Add indexes for known query patterns.
- Avoid destructive operations without safeguards.
- Include rollback/mitigation notes for risky migrations.

## Security and Privacy

- Treat all user input as untrusted.
- Protect against common web vulnerabilities (XSS, CSRF, injection, SSRF, auth bypass).
- Store secrets in environment/config systems, never in source.
- Use least privilege for credentials and service access.
- Log safely: avoid sensitive data in logs.

## Performance

- Start with clear code; optimize hotspots based on evidence.
- Measure before/after for significant performance changes.
- Reduce unnecessary network round-trips and payload size.
- Use caching where it adds clear value and invalidation is defined.

## Observability and Operations

- Add structured logs for key events and failures.
- Emit metrics for request rates, latency, errors, and saturation where available.
- Ensure health/readiness checks are reliable.
- Prefer graceful shutdown and resilient startup behavior.

## Testing Expectations

When tooling exists, run relevant checks before finishing:

- Lint/format check
- Type check
- Unit tests
- Integration/API tests (if present)
- Build verification

Testing guidance:

- Add or update tests for behavior changes.
- Keep tests deterministic and fast.
- Cover edge cases and failure paths for new logic.
- Avoid brittle snapshot-only validation for critical behavior.

## Documentation

Update docs for any changes to:

- Setup/development workflow
- Environment variables or secrets usage
- API contracts or data models
- User-visible behavior

## Git and PR Conventions

- Use focused commits with imperative subject lines.
- Keep PRs scoped; avoid unrelated refactors.
- In PR descriptions include:
  - Summary of change
  - Reasoning/approach
  - Validation performed
  - Risks and rollout/rollback notes (if relevant)

## Branch/Release Safety

- Do not force-push shared protected branches.
- Avoid rewriting history after review unless coordinated.
- Prefer feature flags for risky user-facing changes.

## Agent Behavior Rules

- Do not invent requirements; ask/flag when unclear.
- Do not fabricate test results.
- Do not claim completion without validation steps.
- If blocked, report what was tried, what failed, and next best action.
- Keep final handoff concise and actionable.

## Optional Project-Specific Section (fill in later)

Use this section to define project-specific conventions:

- Tech stack:
- Package manager:
- Commands:
  - Install:
  - Dev:
  - Lint:
  - Typecheck:
  - Test:
  - Build:
- Architecture notes:
- Deployment notes:
- Ownership/contacts:

---

If this template conflicts with explicit task instructions, follow explicit instructions first.
