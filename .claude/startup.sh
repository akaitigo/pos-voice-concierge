#!/usr/bin/env bash
# =============================================================================
# セッション起動ルーチン — pos-voice-concierge
#
# セッション開始時に実行し、ツールの自動インストールとヘルスチェックを行う。
# =============================================================================
set -euo pipefail

SKIP_CHECKS=false

for arg in "$@"; do
  case "$arg" in
    --skip-checks) SKIP_CHECKS=true ;;
  esac
done

echo "=== Session Startup: pos-voice-concierge ==="

[ -d ".git" ] || { echo "ERROR: Not in git repository"; exit 1; }

echo "=== Tool auto-install ==="

# Python (voice-engine)
if [ -f "voice-engine/pyproject.toml" ]; then
  echo "Detected: Python (voice-engine)"
  command -v ruff &>/dev/null || { echo "Installing ruff..."; pip install ruff 2>/dev/null || echo "WARN: ruff install failed"; }
fi

# TypeScript (frontend)
if [ -f "frontend/package.json" ]; then
  echo "Detected: TypeScript (frontend)"
  command -v oxlint &>/dev/null || { echo "Installing oxlint..."; npm install -g oxlint 2>/dev/null || echo "WARN: oxlint install failed"; }
  npx biome --version &>/dev/null 2>&1 || { echo "Installing biome..."; npm install -g @biomejs/biome 2>/dev/null || echo "WARN: biome install failed"; }
fi

# Kotlin (backend)
if [ -f "backend/build.gradle.kts" ]; then
  echo "Detected: Kotlin (backend)"
  if [ -f "backend/gradlew" ]; then
    chmod +x backend/gradlew
  else
    echo "WARN: backend/gradlew not found. Run 'gradle wrapper' in backend/"
  fi
fi

# lefthook
command -v lefthook &>/dev/null || { echo "Installing lefthook..."; go install github.com/evilmartians/lefthook@latest 2>/dev/null || npm install -g lefthook 2>/dev/null || echo "WARN: lefthook install failed"; }
if command -v lefthook &>/dev/null && [ -f "lefthook.yml" ]; then
  lefthook install 2>/dev/null && echo "lefthook hooks installed." || echo "WARN: lefthook install failed"
fi

echo "Tool check complete."

echo "=== Recent commits ==="
git log --oneline -10

if [ "$SKIP_CHECKS" = true ]; then
  echo "=== Health check SKIPPED (--skip-checks) ==="
else
  echo "=== Health check ==="
  echo "Run 'make check' to verify all components."
fi

echo ""
echo "=== Session started at $(date -u +"%Y-%m-%dT%H:%M:%SZ") ==="
echo "Ready to work. State management: git log + GitHub Issues."
