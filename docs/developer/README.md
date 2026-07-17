# ProposalPilot Developer Documentation

このディレクトリは、ProposalPilotの開発者・保守担当者向けドキュメントをまとめる。

## Documents

| File | Purpose |
|---|---|
| `ARCHITECTURE.md` | 全体アーキテクチャと主要コンポーネント |
| `REPOSITORY_GUIDE.md` | 主要ディレクトリの役割 |
| `SEQUENCE_DIAGRAMS.md` | Legacy、Strategy v1、Human Review、Quality Evaluationの流れ |
| `MODULE_DEPENDENCIES.md` | モジュール依存関係と循環参照を避ける方針 |
| `EXTENSION_GUIDE.md` | 将来の拡張ポイント |
| `TROUBLESHOOTING.md` | 開発・運用時のよくある問題 |

## Scope

このドキュメントは、現在の実装を理解し、安全に保守するためのガイドである。

以下は含まない。

- 新しい生成機能の仕様決定
- 本番設定値の実値
- APIキーや秘密情報
- DB変更手順の実行

## Key Principle

Strategy v1は段階的利用を前提とし、既定値はLegacy Engineである。Strategy v1を使う場合も、Human ReviewとQuality Evaluationを通したうえで運用判断する。
