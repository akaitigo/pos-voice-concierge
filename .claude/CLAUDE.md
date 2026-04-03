# アーキテクチャ概要

## 通信フロー
```
Frontend (React) → WebSocket → Backend (Quarkus) → gRPC stream → Voice Engine (Python/Whisper)
```

## backend/ (Kotlin/Quarkus)
- open-posプラグインAPIのエントリポイント
- gRPCクライアント: voice-engineへの音声ストリーミング転送
- WebSocket: フロントエンドとのリアルタイム通信
- PostgreSQL: 商品マスタ・表記ゆれ辞書・売上データへのアクセス
- 依存: `io.quarkus:quarkus-grpc`, `io.quarkus:quarkus-websockets`

## voice-engine/ (Python)
- Whisper: 音声→テキスト変換（tiny/baseモデルでレイテンシ優先）
- ファジーマッチング: rapidfuzz による商品名照合（閾値80%）
- gRPCサーバー: 音声ストリーミングの受信・処理
- 自然言語クエリ: インテント分類（売上照会/在庫照会/商品登録）

## frontend/ (TypeScript/React)
- Web Audio API: マイク入力のキャプチャ
- MediaRecorder: 音声データのチャンク送信
- リアルタイム表示: 認識結果・マッチング候補の即時表示
- Web Speech API: 音声レスポンスの読み上げ（TTS）

## proto/
- `voice_service.proto`: 音声ストリーミングRPC定義
- `query_service.proto`: 自然言語クエリRPC定義

## セキュリティ要件
- 音声データはストリーミング処理のみ（ディスク保存禁止）
- PCI-DSS: カード情報の音声入力は受け付けない
- open-pos SDK公開APIのみ使用（内部API直接アクセス禁止）
- 全通信TLS 1.2+必須
