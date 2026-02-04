# 2. Modular Package Refactor

Date: 2026-02-04

## Status

Accepted

## Context

The project started as a monolithic 890-line script (`connect/migasfree-connect`). This made it difficult to:

- Write unit tests for individual components.
- Maintain and scale features (like adding new protocols).
- Follow standard Python packaging practices.
- Prevent security leaks (like passwords in CLI arguments).

## Decision

We have refactored the monolith into a standard Python package structure:

- Created the `migasfree_connect` package.
- Segmented logic into:
  - `auth`: mTLS and credential handling.
  - `manager`: API client for the Migasfree Manager.
  - `tunnel`: Core WebSocket-to-TCP engine.
  - `launcher`: External client execution.
  - `cli`: Main CLI entry point and remote command logic.
- Adopted `pyproject.toml` for dependency and entry-point management.
- Implemented a `pytest` suite with coverage reporting.
- Hardened security by passing passwords via `stdin` to `openssl`.

## Consequences

- **Improved Testability**: We achieved 82% code coverage immediately after refactoring.
- **Improved Security**: Eliminated potential password leaks in process lists.
- **Maintainability**: Components are now decoupled and reusable.
- **Backward Compatibility**: Kept a small wrapper in `connect/migasfree-connect` for existing tools.
