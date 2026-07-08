# ADR-0003: WebSocket エンドポイントの認証方式

## ステータス

Accepted

## コンテキスト

`/ws/voice` WebSocket エンドポイントは、当初 HTTP 認証ポリシー（`quarkus.http.auth.permission`）が `/api/*` のみを対象としており、`/ws/*` が認証対象から漏れていた（Issue #25）。認証されていないクライアントが音声 WebSocket に接続し、voice-engine への gRPC ストリームを消費できる状態だった。

REST API は `Authorization: Bearer <API_KEY>` ヘッダーで認証している（`ApiKeyAuthMechanism`）。WebSocket にも同一の API キー基盤で認証をかけたいが、次の制約がある:

- ブラウザの標準 `WebSocket` API は、ハンドシェイク（HTTP Upgrade）リクエストに任意のヘッダー（`Authorization` 含む）を設定できない。
- したがって REST と同じ「ヘッダーにトークン」方式をブラウザ WebSocket に直接適用できない。

## 決定

### 1. `/ws/**` を認証必須にする

`application.properties` に HTTP 認証ポリシーを追加し、WebSocket ハンドシェイク（HTTP GET Upgrade）を既存の Quarkus HTTP セキュリティ層で保護する。

```properties
quarkus.http.auth.permission.ws.paths=/ws/*
quarkus.http.auth.permission.ws.policy=authenticated
```

ハンドシェイクは通常の HTTP リクエストとして Vert.x ルーターを通るため、既存の `ApiKeyAuthMechanism` がそのまま適用される。

### 2. WebSocket は `access_token` クエリパラメータでの認証を許可する

`ApiKeyAuthMechanism.resolveApiKey` を次の優先順位に拡張した:

1. 全パス共通で `Authorization: Bearer <key>` ヘッダー（REST・非ブラウザクライアント用）。
2. **`/ws/**` パスに限り** `access_token` クエリパラメータ（ブラウザ WebSocket 用フォールバック）。

クエリパラメータによる認証を WebSocket パスに限定することで、REST エンドポイントでは引き続きヘッダーのみを受け付け、トークンが URL に露出する範囲を最小化する。フロントエンド（`useVoice`）はビルド時に注入された `VITE_POS_VOICE_API_KEY` を `?access_token=` として付与する。

### 検討した代替案

- **`Sec-WebSocket-Protocol`（サブプロトコル）にトークンを載せる**: ブラウザから設定可能でヘッダー方式に近いが、サーバーが選択したサブプロトコルをハンドシェイク応答でエコーバックする必要があり、`@ServerEndpoint` での実装が煩雑。トークンが応答ヘッダーにも現れる。MVP では見送り。
- **Cookie 認証**: CSRF 対策とセッション管理が別途必要になり、ステートレスな API キー方式と整合しない。

## 影響 / リスクと緩和策

- **トークンが URL に載るリスク**: アクセスログ・プロキシログ・ブラウザ履歴にクエリパラメータが残り得る。緩和策:
  - 本番では `wss://`（TLS）必須とし、転送中は URL ごと暗号化する（CLAUDE.md「全通信 TLS 1.2+ 必須」に整合）。
  - リバースプロキシ／アプリのアクセスログで `access_token` クエリをマスクする設定を本番デプロイ時に行う。
  - API キーは `openssl rand -hex 32` 相当の十分なエントロピーを持ち、漏洩時はローテーションする。
- REST エンドポイントの認証面は変更なし（ヘッダーのみ）。`access_token` クエリは `/ws/**` 以外では無視される。
- 将来トークンの短命化（ハンドシェイク専用の一時トークン発行）に移行する余地を残す。移行時は本 ADR を更新する。
