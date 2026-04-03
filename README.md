# pos-voice-concierge

[![CI](https://github.com/akaitigo/pos-voice-concierge/actions/workflows/ci.yml/badge.svg)](https://github.com/akaitigo/pos-voice-concierge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

音声でPOSを操作する拡張プラグイン。店舗スタッフがマイクに向かって商品名を発話するだけで商品登録・売上照会・在庫確認ができる。

## デモ

> デモGIFは初回デプロイ後に追加予定

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| Frontend | TypeScript, React 19, Vite, Web Audio API, Web Speech API (TTS) |
| Backend | Kotlin, Quarkus 3.34, gRPC, WebSocket, Flyway, PostgreSQL |
| Voice Engine | Python 3.12, OpenAI Whisper (base), rapidfuzz, gRPC |
| CI/CD | GitHub Actions (3ジョブ並列), Dependabot + auto-merge |
| Lint/Format | detekt (Kotlin), Ruff (Python), oxlint + Biome (TypeScript) |
| Proto | Protocol Buffers 3, gRPC双方向ストリーミング |

## アーキテクチャ

```
Browser (React)
  |  Web Audio API / MediaRecorder
  |  WebM/Opus chunks
  |
  v  WebSocket (binary frames)
Backend (Kotlin/Quarkus)
  |  AudioChunk proto
  |
  v  gRPC Bidirectional Stream
Voice Engine (Python/Whisper)
  |  音声認識 -> ファジーマッチング -> インテント分類
  |
  v  RecognitionResult / QueryResponse proto
Backend -> WebSocket -> Browser
  |
  v  Web Speech API (TTS) で音声応答
```

### 主な機能

- **音声認識による商品登録** -- Whisper base モデル + gRPC ストリーミングでリアルタイム認識
- **商品名ファジーマッチング** -- rapidfuzz WRatio による日本語表記ゆれ対応（閾値80%）
- **自然言語クエリ** -- 「今日の売上は？」「牛乳の在庫は？」で売上・在庫を即時照会
- **音声レスポンス** -- Web Speech API TTS で結果を読み上げ
- **表記ゆれ辞書の自動学習** -- ユーザー修正をトリガーにエイリアスを自動登録

## クイックスタート

### 前提条件

- Java 21 (Temurin 推奨)
- Python 3.12+
- Node.js 22+
- PostgreSQL 15+
- ffmpeg (音声変換用)

### 1. リポジトリのクローン

```bash
git clone https://github.com/akaitigo/pos-voice-concierge.git
cd pos-voice-concierge
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して以下を設定:
#   DATABASE_URL=jdbc:postgresql://localhost:5432/pos_voice_concierge
#   DATABASE_USER=postgres
#   DATABASE_PASSWORD=<your-password>
#   BACKEND_PORT=8080
#   VOICE_ENGINE_HOST=localhost
#   VOICE_ENGINE_PORT=50051
```

### 3. データベースの準備

```bash
createdb pos_voice_concierge
```

### 4. Voice Engine (Python) の起動

```bash
cd voice-engine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pos_voice_concierge.grpc_server
```

### 5. Backend (Kotlin/Quarkus) の起動

```bash
cd backend
./gradlew quarkusDev
```

### 6. Frontend (React) の起動

```bash
cd frontend
npm ci
npm run dev
```

ブラウザで http://localhost:5173 を開き、マイクボタンを押して商品名を発話する。

## 開発

```bash
# 全チェック (format -> lint -> test -> build)
make check

# 個別実行
make test-backend    # Kotlin テスト
make test-voice      # Python テスト
make test-frontend   # TypeScript テスト
make lint            # 全リンター
make format          # 全フォーマッター
```

### ディレクトリ構成

```
pos-voice-concierge/
  backend/         Kotlin/Quarkus (プラグインAPI + gRPC + WebSocket)
  voice-engine/    Python (Whisper音声認識 + ファジーマッチング)
  frontend/        TypeScript/React (音声UI + 確認画面)
  proto/           gRPC定義ファイル (voice_service.proto, query_service.proto)
  docs/            ADR, PRD
  .github/         CI/CD ワークフロー
```

### ADR (Architecture Decision Records)

技術的な意思決定は `docs/adr/` に記録している。

- [ADR-0001: 音声ストリーミングパイプラインアーキテクチャ](docs/adr/0001-voice-streaming-pipeline-architecture.md)
- [ADR-0002: ファジーマッチングアルゴリズム選定](docs/adr/0002-fuzzy-matching-algorithm-selection.md)

## ライセンス

[MIT](LICENSE)
