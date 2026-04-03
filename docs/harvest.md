# Harvest（振り返り） — pos-voice-concierge

実施日: 2026-04-03

## 1. プロジェクト概要

| 項目 | 値 |
|------|-----|
| リポジトリ | akaitigo/pos-voice-concierge |
| 概要 | open-posに音声インターフェースを追加するプラグイン |
| 技術スタック | Kotlin/Quarkus + Python/Whisper + TypeScript/React |
| 開始日 | 2026-04-03 22:52 JST |
| 完了日 | 2026-04-04 00:50 JST |
| 実質所要時間 | 約2時間 |
| バージョン | v1.0.0 |

## 2. メトリクス

### Issue / PR

| メトリクス | 値 |
|-----------|-----|
| Issue 総数 | 5 |
| Issue クローズ数 | 5 |
| Issue 完了率 | 100% |
| PR 総数 | 11 |
| PR マージ数 | 6 |
| PR オープン（Dependabot） | 5 |
| PR マージ率（手動PR） | 100% (6/6) |

### コードベース

| メトリクス | 値 |
|-----------|-----|
| 総変更行数 | +14,252 / -203 |
| ファイル数 | 87 |
| Kotlin (backend) | 34 ファイル / 2,466 行 |
| Python (voice-engine) | 21 ファイル / 3,309 行 |
| TypeScript (frontend) | 22 ファイル / 2,605 行 |
| 合計コード行数 | 8,380 行 |

### テスト

| コンポーネント | テスト数 | カバレッジ |
|---------------|---------|-----------|
| Backend (Kotlin/Quarkus) | 16 | - |
| Voice Engine (Python) | 148 | 80% |
| Frontend (TypeScript/React) | 84 | - |
| **合計** | **248** | - |

### CI/CD

| メトリクス | 値 |
|-----------|-----|
| CI 実行回数 | 30 |
| 成功 | 22 |
| 失敗 | 4（全て Dependabot PR） |
| スキップ | 4 |
| CI 成功率（手動PR） | 100% |

### ハーネス適用状況

| 項目 | 状態 | 備考 |
|------|------|------|
| CLAUDE.md | 47行 | 50行制限以内 |
| .claude/CLAUDE.md | 存在 | アーキテクチャ詳細を分離 |
| .claude/settings.json | 存在 | PreToolUse / PreCompact / Stop フック |
| .claude/startup.sh | 存在 | ツール自動インストール + ヘルスチェック |
| lefthook.yml | 存在 | format / lint / test / archgate |
| ADR | 2件 | 音声パイプライン / ファジーマッチング |
| PRD | 1件 | docs/PRD.md |
| Makefile | 存在 | build / test / lint / format / check / quality |
| CI (GitHub Actions) | 2ワークフロー | ci.yml + auto-merge-dependabot.yml |
| LICENSE | MIT | 存在 |
| README.md | 存在 | Ship フェーズで整備済み |
| CHANGELOG.md | 存在 | v1.0.0 |

## 3. うまくいったこと

### 3-1. マルチ言語モノレポの一発立ち上げ
Kotlin + Python + TypeScript の3言語構成にもかかわらず、Makefile で統一コマンド（`make build` / `make test` / `make lint`）を提供し、言語の違いを吸収できた。lefthook で pre-commit に全言語の lint + test を統合したことで、品質ゲートが最初から機能した。

### 3-2. ADR駆動の技術選定
音声ストリーミングパイプラインアーキテクチャ（ADR-0001）とファジーマッチングアルゴリズム選定（ADR-0002）を実装前に書いたことで、Whisper モデルサイズ・gRPC vs REST・rapidfuzz vs 他ライブラリの判断根拠が明文化され、後から「なぜこの設計なのか」の問い合わせが発生しなかった。

### 3-3. テストカバレッジの充実
248テスト（Backend 16 + Voice Engine 148 + Frontend 84）を機能と同時に書き、Voice Engine は80%カバレッジを達成。特にファジーマッチング・インテント分類・クエリサービスのテストが手厚く、リファクタリング時の安全ネットとして機能した。

### 3-4. CI安定性
手動PRのCI成功率100%。Dependabot PRの失敗はメジャーバージョンアップ（vitest 2→4, biome 1→2, TypeScript 5→6）が原因で、プロジェクトコードの問題ではなかった。CI構成は3ジョブ並列（Backend / Voice Engine / Frontend）で効率的に回った。

### 3-5. Hooks によるセキュリティガードレール
.claude/settings.json の PreToolUse フックで以下を自動ブロックした:
- 機密ファイル（.env等）への書き込み
- PCI-DSS違反（カード情報のログ出力）
- 破壊的コマンド（rm -rf, git push --force等）
- --no-verify フック回避

## 4. 改善すべきこと

### 4-1. Backend テストの薄さ
Voice Engine（148テスト）・Frontend（84テスト）と比較して、Backend は16テストと明らかに薄い。特にWebSocket統合テストとgRPCクライアントのエッジケーステストが不足。カバレッジ計測も未設定。

### 4-2. Dependabot PRの放置
5件のDependabot PR（oxlint, biome, vitest, vitest/coverage-v8, TypeScript）がCI失敗のままオープン状態。メジャーバージョンアップは手動対応が必要だが、auto-merge ワークフローがマイナー/パッチのみ対象のため、メジャーアップデートへの対応方針が未定義。

### 4-3. E2Eテストの欠如
Frontend → Backend → Voice Engine の結合テスト・E2Eテストが存在しない。各コンポーネントのユニットテストは充実しているが、WebSocket + gRPC を跨いだ統合テストがなく、デプロイ後の挙動を保証できない。

### 4-4. 環境構築手順の不足
Docker Compose やローカル開発環境のセットアップ手順が不十分。PostgreSQL、Python venv、Node.js、JDK 21 の各依存をどの順序でインストールするかが README に網羅されていない。

### 4-5. proto 管理の未成熟
buf.yaml が存在せず、proto ファイルの lint / breaking change 検証が CI に組み込まれていない。voice_service.proto と query_service.proto の変更が後方互換性を壊すリスクがある。

## 5. 次のPJへの教訓

### 5-1. proto ファイルは初日から buf で管理する
gRPC を使うプロジェクトでは、buf.yaml + buf.gen.yaml を初期セットアップに含め、CI に `buf lint` + `buf breaking` を組み込む。今回は手動でコード生成したが、buf generate で自動化すべきだった。

### 5-2. Dependabot のメジャーバージョン戦略を事前に決める
auto-merge ワークフローのスコープ（patch/minor のみ vs メジャー含む）と、メジャーバージョンアップ時の対応手順（誰がいつ対応するか）を CLAUDE.md またはCONTRIBUTING.md に明記する。

### 5-3. マルチ言語プロジェクトでは Docker Compose を初日から用意する
3言語の依存管理が複雑になるため、`docker-compose.yml` で PostgreSQL + Backend + Voice Engine + Frontend を一発起動できる環境を初期構築に含める。

### 5-4. Backend テストを声明的に最低ラインを設ける
「テストを書く」だけでなく、各コンポーネントの最低テスト数やカバレッジ閾値を quality ゲートに組み込む。今回は Backend のテスト不足を質的に見落とした。

### 5-5. 統合テスト戦略を ADR にする
E2Eテストの技術選定（Testcontainers, WireMock, Playwright等）と実行タイミング（PR / nightly）を ADR として記録し、MVP完了前に最低1本の統合テストを必須にする。

## 6. テンプレート改善提案

| 対象ファイル | 変更内容 | 根拠 |
|-------------|---------|------|
| CLAUDE.md テンプレート | proto/ 使用時の `buf lint` / `buf breaking` コマンドをワークフローセクションに追加 | gRPC プロジェクトで buf 管理が漏れた |
| Makefile テンプレート | `proto-lint` / `proto-breaking` ターゲットを追加 | proto ファイル変更時の CI 検証が未実装だった |
| ci.yml テンプレート | proto lint / breaking change ジョブを追加 | CI で proto の後方互換性が検証されなかった |
| Makefile テンプレート | `quality` ターゲットにコンポーネント別最低テスト数チェックを追加 | Backend のテスト不足を自動検出できなかった |
| .claude/startup.sh テンプレート | `buf` の自動インストールを追加 | gRPC 使用時に buf が未インストールのまま開発が進んだ |
| CLAUDE.md テンプレート | Dependabot メジャーバージョン対応方針セクションを追加 | メジャーアップデート PR が放置された |
| idea-launch テンプレート | Docker Compose スケルトン生成をマルチ言語検出時に自動追加 | 環境構築手順が不足した |
| ci.yml テンプレート | Dependabot PR でのメジャーバージョン失敗時に Issue 自動作成 | CI 失敗 PR が通知なく放置された |

## 7. CI/CD で困ったこと

| 問題 | 影響 | 対応 |
|------|------|------|
| Dependabot メジャーバージョンアップの CI 失敗 | 5 PR がオープンのまま放置 | auto-merge はマイナー/パッチのみ。メジャーは手動対応が必要だが方針未定義 |
| 3言語並列 CI の実行時間 | 各ジョブ 1-2 分だが合計で CI 完了まで待つ必要 | concurrency + cancel-in-progress で重複排除。十分速い |
| proto コード生成の CI 未統合 | proto 変更後の生成コード不整合リスク | buf generate を CI に組み込んで差分チェックすべき |

## 8. サマリー

### 統計
- **2時間** で 3言語 / 8,380行 / 248テスト の MVP を完成
- Issue 完了率 **100%**（5/5）、手動PR マージ率 **100%**（6/6）
- CI 全グリーン（手動PR）、v1.0.0 タグ付与済み

### テンプレート改善のキーポイント
1. **gRPC/proto プロジェクトでは buf を初日から統合する** — proto lint + breaking change 検証の CI 組み込み
2. **コンポーネント別テスト閾値を quality ゲートに追加する** — テスト不足の自動検出
3. **Dependabot メジャーバージョン対応方針をテンプレートに含める** — 放置 PR の防止

### 次のPJへの申し送り
- マルチ言語プロジェクトでは Docker Compose を初日から用意する
- E2Eテスト戦略は ADR で決定し、MVP 前に最低1本は実装する
- Backend（サーバーサイド）のテスト品質は意識的に高めないと薄くなりやすい
- proto ファイルがある場合は buf.yaml + buf.gen.yaml をプロジェクト初期化に含める
