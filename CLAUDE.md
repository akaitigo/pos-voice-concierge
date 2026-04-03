# pos-voice-concierge

## コマンド
- ビルド: `make build`
- テスト: `make test`
- lint: `make lint`
- フォーマット: `make format`
- 全チェック: `make check`

## ワークフロー
1. research.md を作成（調査結果の記録）
2. plan.md を作成（実装計画。人間承認まで実装禁止）
3. 承認後に実装開始。plan.md のtodoを進捗管理に使用

## 構造
- backend/ — Kotlin/Quarkus (プラグインAPI + gRPC)
- voice-engine/ — Python (Whisper音声認識 + ファジーマッチング)
- frontend/ — TypeScript/React (音声UI + 確認画面)
- proto/ — gRPC定義ファイル

## ルール
- ADR: docs/adr/ 参照。新規決定はADRを書いてから実装
- テスト: 機能追加時は必ずテストを同時に書く
- lint設定の変更禁止（ADR必須）
- open-pos SDK: `@open-pos/sdk` の公開APIのみ使用
- PCI-DSS: カード情報のログ出力・localStorage保存 絶対禁止
- 音声データ: サーバー側に永続化しない（ストリーミング処理のみ）

## 禁止事項
- any型(TS) / !!(Kotlin) → 各言語ルール参照
- console.log / print文のコミット
- TODO コメントのコミット（Issue化すること）
- .env・credentials のコミット
- eval() / Function() コンストラクタ
- localStorage への機密情報保存

## Hooks
- 設定: .claude/hooks/ 参照
- 構造定義: docs/hooks-structure.md 参照

## 状態管理
- git log + GitHub Issues でセッション間の状態を管理
- セッション開始: `bash .claude/startup.sh`

## コンテキスト衛生
- .gitignore / .claudeignore で不要ファイルを除外
- 1000行超のファイルはシグネチャのみ参照
