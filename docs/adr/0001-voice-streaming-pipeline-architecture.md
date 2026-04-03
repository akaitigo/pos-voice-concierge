# ADR-0001: 音声ストリーミングパイプラインアーキテクチャ

## ステータス

Accepted

## コンテキスト

POS Voice Concierge は、店舗スタッフがマイクで商品名を発話し、リアルタイムで音声認識・商品照合を行うシステムである。以下の技術選定が必要:

1. 音声認識モデルの選定（サイズ・精度・レイテンシのトレードオフ）
2. フロントエンド↔バックエンド間の通信プロトコル
3. バックエンド↔音声エンジン間の通信プロトコル
4. 音声データの処理方式（バッチ vs ストリーミング）

### 制約

- POS端末での利用を想定し、レイテンシ p95 < 3s が必須
- 音声データはセキュリティ上、サーバー側に永続化しない
- Voice Engine は Python（Whisper の公式実装が Python のみ）
- Backend は Kotlin/Quarkus（既存アーキテクチャ）

## 決定

### 1. Whisper モデルサイズ: `base`

| モデル | パラメータ数 | 相対速度 | 日本語 WER |
|--------|------------|---------|-----------|
| tiny   | 39M        | ~32x    | 高い       |
| base   | 74M        | ~16x    | 中程度     |
| small  | 244M       | ~6x     | 低い       |
| medium | 769M       | ~2x     | 最低       |

`base` を選定。理由:
- `tiny` は日本語の認識精度が不十分（商品名の誤認識が多い）
- `small` 以上はレイテンシが 3s を超えるリスクがある
- `base` は精度とレイテンシのバランスが最も良い
- 精度不足はファジーマッチング（rapidfuzz, 閾値80%）で補完する設計

### 2. フロントエンド↔バックエンド: WebSocket

**候補:**
- WebSocket: 双方向・低レイテンシ・バイナリ対応
- SSE (Server-Sent Events): サーバー→クライアント片方向のみ
- HTTP/2 Streaming: ブラウザサポートが限定的

**選定理由:**
- 音声データの送信（クライアント→サーバー）と認識結果の返却（サーバー→クライアント）を同一コネクションで行える
- バイナリデータ（音声チャンク）の送受信に対応
- ブラウザの Web Audio API / MediaRecorder との親和性が高い
- SSE はクライアント→サーバーの音声送信に別チャネルが必要で複雑化する
- Quarkus が `quarkus-websockets` で標準サポート

### 3. バックエンド↔Voice Engine: gRPC 双方向ストリーミング

**候補:**
- gRPC Bidirectional Streaming: 型安全・ストリーミングネイティブ
- REST + Polling: シンプルだがレイテンシが高い
- WebSocket: 型定義が弱い

**選定理由:**
- Protocol Buffers による厳密な型定義（AudioChunk, RecognitionResult）
- 双方向ストリーミングで中間結果をリアルタイム返却できる
- Quarkus gRPC（Mutiny Multi）と grpcio（Python）の成熟したエコシステム
- HTTP/2 ベースで多重化・フロー制御が組み込み
- 中間結果（is_final=false）を逐次返すことでUXを向上

### 4. 音声処理: ストリーミングのみ（ファイル保存なし）

- 音声データはメモリ上のバッファのみで処理
- WebM/Opus → WAV 変換は Voice Engine 側で ffmpeg/pydub を使用
- 変換後の WAV もメモリ上で処理し、ディスクに書き出さない
- セキュリティ要件（PCI-DSS 準拠）とプライバシー保護を両立

## パイプライン全体図

```
Browser (Web Audio API)
  │ MediaRecorder: WebM/Opus chunks
  │
  ▼ WebSocket (binary frames)
Backend (Quarkus)
  │ ByteArray → AudioChunk proto
  │
  ▼ gRPC Bidirectional Stream
Voice Engine (Python)
  │ WebM/Opus → WAV (in-memory)
  │ Whisper base model inference
  │ FuzzyMatcher product matching
  │
  ▼ RecognitionResult proto
Backend → WebSocket → Browser
```

## 影響

- Voice Engine は GPU なしでも動作するが、GPU があればレイテンシが大幅に改善する
- `base` モデルで精度不足の場合は `small` への切り替えを検討（ADR 更新が必要）
- WebSocket はステートフルなため、Backend のスケールアウト時にセッションアフィニティが必要
- gRPC の TLS 設定は本番環境デプロイ時に別途対応する
