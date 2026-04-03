# Hooks 設計 — pos-voice-concierge

## 構造

| Hook | 目的 |
|------|------|
| PreToolUse (Edit/Write) | 機密ファイル保護 + PCI-DSS違反検出 |
| PreToolUse (Bash) | 破壊的コマンド + --no-verify ブロック |
| PreCompact | CLAUDE.md バックアップ |
| Stop | open-pos互換性チェック |

## 詳細

設定ファイル: `.claude/settings.json`
PostToolUseスクリプト: `scripts/post-lint.sh`（Python/TS/Kotlin対応）
