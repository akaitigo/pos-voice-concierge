#!/usr/bin/env bash
set -euo pipefail

input="$(cat)"
file="$(jq -r '.tool_input.file_path // .tool_input.path // empty' <<< "$input")"

# Python files
case "$file" in
  *.py)
    cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$file")"
    ruff check --fix "$file" >/dev/null 2>&1 || true
    ruff format "$file" >/dev/null 2>&1 || true
    diag="$(ruff check "$file" 2>&1 | head -20)"
    if [ -n "$diag" ]; then
      jq -Rn --arg msg "$diag" \
        '{ hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: $msg } }'
    fi
    exit 0
    ;;
  *.ts|*.tsx|*.js|*.jsx)
    cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$file")"
    npx biome format --write "$file" >/dev/null 2>&1 || true
    npx oxlint --fix "$file" >/dev/null 2>&1 || true
    diag="$(npx oxlint "$file" 2>&1 | head -20)"
    if [ -n "$diag" ]; then
      jq -Rn --arg msg "$diag" \
        '{ hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: $msg } }'
    fi
    exit 0
    ;;
  *.kt|*.kts)
    cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$file")"
    if [ -f "backend/gradlew" ]; then
      diag="$(cd backend && ./gradlew detekt 2>/dev/null | tail -5 || true)"
      if echo "$diag" | grep -q "BUILD FAILED"; then
        jq -Rn --arg msg "$diag" \
          '{ hookSpecificOutput: { hookEventName: "PostToolUse", additionalContext: $msg } }'
      fi
    fi
    exit 0
    ;;
esac
