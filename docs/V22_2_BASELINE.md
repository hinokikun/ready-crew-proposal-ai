# Version 22.2 Baseline

取得日: 2026-07-14

## 変更前コマンド結果

| 項目 | 結果 |
| --- | --- |
| `npm.cmd run typecheck` | 成功 |
| `npm.cmd run check:unused` | 成功 |
| `npm.cmd run build` | 成功 |
| `npm.cmd run test:e2e` | 成功: 29 tests |
| `python -m compileall app tests` | 成功 |
| `pytest -q` | 成功: 139 tests |
| `pip check` | 成功 |
| `git diff --check` | 成功 |

## 変更前サイズ

| ファイル | 行数 |
| --- | ---: |
| `frontend/components/AppShell.tsx` | 5101 |
| `backend/app/services/pptx_service.py` | 1218 |

## Frontend Build

| 指標 | 値 |
| --- | ---: |
| Build time | 3.7s |
| `/` size | 3.22 kB |
| First Load JS | 106 kB |
| Shared JS | 103 kB |
| Route handlers | 0 |

## PPTX Baseline

### Detailed PPTX

- bytes: 54309
- slide count: 13
- slide size: 12191695 x 6858000
- total shapes: 217

| # | title | shapes | tables |
| ---: | --- | ---: | ---: |
| 1 | UX | 25 | 0 |
| 2 | Chapter 02 | 12 | 0 |
| 3 | COMPETITOR | 14 | 1 |
| 4 | Chapter 03 | 12 | 0 |
| 5 | 実績紹介 | 19 | 0 |
| 6 | Chapter 04 | 12 | 0 |
| 7 | ESTIMATE | 10 | 1 |
| 8 | Chapter 05 | 12 | 0 |
| 9 | BUDGET FIT | 33 | 0 |
| 10 | Chapter 06 | 12 | 0 |
| 11 | SCOPE | 16 | 0 |
| 12 | Chapter 07 | 12 | 0 |
| 13 | 商談判断 | 28 | 0 |

### Summary PPTX

- bytes: 55069
- slide count: 11
- slide size: 12191695 x 6858000
- total shapes: 342

| # | title | shapes | tables |
| ---: | --- | ---: | ---: |
| 1 | UX | 25 | 0 |
| 2 | SUMMARY | 32 | 0 |
| 3 | 顧客理解 | 31 | 0 |
| 4 | 課題整理 | 39 | 0 |
| 5 | 提案方針 | 29 | 0 |
| 6 | STRATEGY | 33 | 0 |
| 7 | サイトマップ | 49 | 0 |
| 8 | 成果設計 | 24 | 1 |
| 9 | スケジュール | 27 | 0 |
| 10 | 費用概算 | 11 | 1 |
| 11 | NEXT STEP | 42 | 0 |

## Notes

- 変更前から作業ツリーには多数の未コミット変更が存在していた。
- Version 22.2ではUI/API/DB仕様を変更しない前提で分割と回帰テストを追加する。
