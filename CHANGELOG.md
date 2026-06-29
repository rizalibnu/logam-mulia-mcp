# Changelog

All notable changes to this project documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pre-commit hooks: ruff lint + format, pytest on commit
- GitHub Actions: test, PyPI publish, and GitHub Release on tag push
- Optional `LOGAM_MULIA_BASE_URL` env shown in Claude Code & Hermes integration examples

## [1.0.1] — 2026-06-29

### Fixed
- Test version match after bump
- Build config (setuptools packages.find `where`)

## [1.0.0] — 2026-06-29

### Added
- Initial public release
- `get_price(source, refresh?)` — latest price from any source
- `get_price_history(source, page?, length?, weight?, material?, material_type?)` — paginated price history
- `list_sources()` — all 18 available price sources
- `get_all_prices()` — latest prices from all sources at once
- `get_news()` — latest gold news from Investor ID
- `get_news_detail(url)` — full article text
- PyPI package with `uvx` entry point
- MIT license
- Unit test suite with pytest

[//]: # (Versions are references for comparison links — collapsed until a proper versioned release tag exists.)
[unreleased]: https://github.com/rizalibnu/logam-mulia-mcp/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/rizalibnu/logam-mulia-mcp/releases/tag/v1.0.1
[1.0.0]: https://github.com/rizalibnu/logam-mulia-mcp/releases/tag/v1.0.0
