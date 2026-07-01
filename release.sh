#!/usr/bin/env bash
set -euo pipefail

# ── Logam Mulia MCP — automated release script ──────────────────────────
#
# Usage:
#   ./release.sh           # print current version
#   ./release.sh bump patch   # 1.2.0 → 1.2.1
#   ./release.sh bump minor   # 1.2.0 → 1.3.0
#   ./release.sh bump major   # 1.2.0 → 2.0.0
#
# Does: bump version → update CHANGELOG → commit → tag → push (triggers CI)
# ──────────────────────────────────────────────────────────────────────────

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

SERVER_PY="$ROOT/src/logam_mulia_mcp/server.py"
PYPROJ="$ROOT/pyproject.toml"
CHANGELOG="$ROOT/CHANGELOG.md"

# ── helpers ──────────────────────────────────────────────────────────────

fmt() { printf "\033[1;32m%s\033[0m\n" "$*"; }
die() { printf "\033[1;31m%s\033[0m\n" "$*" >&2; exit 1; }

# ── read current version (from server.py — single source of truth) ───────

current_version=$(grep -oP '__version__\s*=\s*"\K[^"]+' "$SERVER_PY")
[[ -n "$current_version" ]] || die "Cannot read version from $SERVER_PY"

fmt "Current version: $current_version"

# ── print only mode ──────────────────────────────────────────────────────

if [[ $# -eq 0 ]]; then
  echo "$current_version"
  exit 0
fi

# ── bump ─────────────────────────────────────────────────────────────────

if [[ "${1:-}" != "bump" || -z "${2:-}" ]]; then
  die "Usage: $0 [bump patch|minor|major]"
fi

PART="$2"
case "$PART" in
  patch|minor|major) ;;
  *) die "PART must be one of: patch, minor, major" ;;
esac

IFS='.' read -r -a parts <<< "$current_version"
major="${parts[0]}"
minor="${parts[1]}"
patch="${parts[2]}"

case "$PART" in
  patch) patch=$((patch + 1)) ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  major) major=$((major + 1)); minor=0; patch=0 ;;
esac

new_version="${major}.${minor}.${patch}"
today=$(date +%Y-%m-%d)

fmt "New version:  $new_version"

# ── update server.py ─────────────────────────────────────────────────────

sed -i "s/__version__ = \"$current_version\"/__version__ = \"$new_version\"/" "$SERVER_PY"
fmt "  ✓ server.py"

# ── update pyproject.toml ────────────────────────────────────────────────

sed -i "s/^version = \"$current_version\"/version = \"$new_version\"/" "$PYPROJ"
fmt "  ✓ pyproject.toml"

# ── update CHANGELOG.md ──────────────────────────────────────────────────

# Replace "## [Unreleased]" with "## [Unreleased]\n\n## [$new_version] — $today"
# And add version comparison link for the new version
if grep -q "^## \[Unreleased\]" "$CHANGELOG"; then
  # First, replace the placeholder
  sed -i "/^## \[Unreleased\]$/a\\\n## [$new_version] — $today" "$CHANGELOG"

  # Add version link entry (right before the [//]: # block)
  prev_tag="v$current_version"
  new_tag="v$new_version"
  link_line="[$new_version]: https://github.com/rizalibnu/logam-mulia-mcp/releases/tag/$new_tag"
  sed -i "/^\[unreleased\]:/a\\$link_line" "$CHANGELOG"

  # Update unreleased compare link to point to new tag
  sed -i "s|compare/v$current_version...HEAD|compare/$new_tag...HEAD|" "$CHANGELOG"
  fmt "  ✓ CHANGELOG.md"
else
  fmt "  ⚠ CHANGELOG.md [Unreleased] section not found — update manually"
fi

# ── commit & tag & push ──────────────────────────────────────────────────

fmt ""
fmt "Committing..."
git add "$SERVER_PY" "$PYPROJ" "$CHANGELOG"
git commit -m "chore: bump to $new_version"

fmt "Tagging v$new_version..."
git tag "v$new_version"

fmt "Pushing..."
git push origin master --tags

fmt ""
fmt "✔ Released $current_version → $new_version"
fmt "   → CI will publish to PyPI and create GitHub Release"
fmt "   → https://github.com/rizalibnu/logam-mulia-mcp/releases"
