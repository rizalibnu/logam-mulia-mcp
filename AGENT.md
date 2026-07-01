# Logam Mulia MCP — Agent Guide

## Project

MCP server for Indonesian gold prices. Single Python package at `src/logam_mulia_mcp/`.

## Conventions

- **Version**: single source of truth in `src/logam_mulia_mcp/server.py` `__version__`, mirrored in `pyproject.toml`
- **CHANGELOG**: `CHANGELOG.md` — Keep a Changelog format. Unreleased section under `## [Unreleased]`
- **Tests**: `tests/` — pytest, asyncio mode auto, mock `_api_get` for HTTP
- **Pre-commit**: ruff lint + format, pytest — run before every commit
- **CI**: GitHub Actions on master push + tag push (`v*`)

## Release workflow

1. Update `__version__` in `server.py` + `pyproject.toml`
2. Update `CHANGELOG.md` — move Unreleased to new version, add date
3. Commit: `chore: bump to X.Y.Z`
4. Tag: `git tag vX.Y.Z`
5. Push: `git push origin master --tags`
6. CI handles PyPI publish + GitHub Release

Or use `./release.sh bump minor` for automated flow (version bump → changelog → commit → tag → push).

## Key files

| File | Purpose |
|------|---------|
| `src/logam_mulia_mcp/server.py` | Main MCP server — all tools, version |
| `tests/test_server.py` | Test suite |
| `pyproject.toml` | Build, deps, tool config |
| `CHANGELOG.md` | Release history |
| `release.sh` | Automated release script |

## Dynamic sources

Price sources are fetched live from `/api/prices` endpoint with 5-min cache in `_sources_cache`. No hardcoded list — always current.
