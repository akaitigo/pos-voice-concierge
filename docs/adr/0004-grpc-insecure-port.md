# ADR-0004: Backend ↔ Voice Engine 間 gRPC の insecure port 使用

## ステータス

Accepted

## コンテキスト

Backend（Quarkus）と Voice Engine（Python）間は gRPC 双方向ストリーミングで通信する（ADR-0001）。現状の実装は平文（insecure）で接続している:

- Voice Engine 側: `grpc_server.py` の `server.add_insecure_port(f"[::]:{port}")`
- Backend 側: `quarkus.grpc.clients.voice-engine.host/port`（TLS 設定なし）

CLAUDE.md には「全通信 TLS 1.2+ 必須」とあり、この設計判断が ADR に記録されていなかった（Issue #30）。本 ADR で現状の設計判断・リスク・本番移行計画を明文化する。

## 決定

MVP 段階では、Backend ↔ Voice Engine 間の gRPC を **insecure port** で運用する。

### 理由

- Backend と Voice Engine は同一ホスト／同一プライベートネットワーク（例: Kubernetes の Pod 内 localhost、または同一 namespace 内サービス）での内部通信を前提とする。外部公開はしない。
- mTLS 証明書の発行・ローテーション・配布は運用コストが高く、MVP のスコープ外。
- 外部公開される通信（ブラウザ ↔ Backend の WebSocket）は別途 TLS（wss://）で保護する（ADR-0003）。TLS 必須ポリシーの主対象はこの外部境界である。

### 本番移行時の対応

内部ネットワークが信頼境界にならない構成（マルチテナント、ネットワーク分離が不十分な環境）へ移行する場合、以下を実施し本 ADR を更新する:

1. Voice Engine 側を `server.add_secure_port` + `grpc.ssl_server_credentials`（サーバー証明書、必要に応じて mTLS のクライアント証明書検証）に切り替える。
2. Backend 側 `quarkus.grpc.clients.voice-engine.ssl.*`（trust-store / key-store）で secure channel を構成する。
3. 証明書は環境変数／シークレットマネージャで注入し、ローテーション手順を整備する。
4. サービスメッシュ（例: Istio mTLS）で透過的に暗号化する選択肢も検討する。

## リスクと緩和策

- **リスク**: 内部ネットワークでの中間者攻撃（MITM）・盗聴。内部通信が平文のため、ネットワークに侵入した攻撃者は音声認識結果や集計データを傍受・改竄し得る。
- **緩和策（MVP）**:
  - gRPC ポートを外部に公開しない（内部ネットワーク／localhost バインドに限定）。
  - ネットワークポリシー（例: Kubernetes NetworkPolicy）で Backend からのアクセスのみ許可する。
  - 音声データはストリーミング処理のみでディスクに永続化しない（ADR-0001）ため、傍受されても保存リスクは限定的。
- 上記が満たせない環境では、本番移行時の対応（mTLS 化）を必須とする。
