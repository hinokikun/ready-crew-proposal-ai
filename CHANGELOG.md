# Changelog

## [1.0.0-rc1] - 2026-07-09

### Changed
- `page.tsx` を薄いエントリにし、アプリ本体を `components/AppShell.tsx` へ移動。
- Backendの会社URL調査、入力メタ情報処理をservicesへ分離。
- SQLite接続をSQLAlchemy engine経由に整理。
- Frontendの管理・認証・CRM型を `types/app.ts` へ集約。
- Header / Dashboard をメモ化し、初期表示をdynamic import化。

### Added
- pytestによる認証、権限、提案生成、PPTX、要約PPTX、PDF、CRM、監査ログのテスト。
- 管理者向けAudit Log APIと画面表示。
- 共通StatusMessage UI。
- GitHub Issue / PRテンプレート、LICENSE、CONTRIBUTING。

### Security
- 監査ログはログイン、生成、保存、設定変更のみを記録。
- 入力本文全文、生成本文全文、APIキー、パスワードは監査ログに保存しない方針を明記。
