# Changelog

## v1.0.0 (2026-04-03)

### Features
- 音声認識による商品登録（Whisper + gRPCストリーミング）
- 商品名ファジーマッチング（日本語表記ゆれ対応）
- 自然言語クエリ（売上・在庫照会）
- 音声レスポンス（Web Speech API TTS）
- 表記ゆれ辞書の自動学習

### Infrastructure
- GitHub Actions CI（backend/voice-engine/frontend 3ジョブ並列）
- Dependabot + auto-merge設定
