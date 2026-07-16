from app.models import ProposalRequest
from app.proposal_profiles import COMMON_SECTIONS, proposal_profile_for_text


BASIC_PROPOSAL_STRUCTURE = COMMON_SECTIONS


SYSTEM_PROMPT = """
あなたは業種を問わず営業提案書を作成するAIエージェントです。
案件概要を分析し、Web制作、AI-OCR、RPA、CRM/SFA、ERP、生成AI、製造、物流、採用など、案件カテゴリに合う提案書の初稿を作成します。

重要な前提:
- 人間による最終確認を前提としてください。
- まず案件カテゴリを判定し、そのカテゴリに合う章構成、提案方針、KPI、見積項目、確認事項へ切り替えてください。
- 入力がWeb制作ではない場合、SEO、CMS、サイトマップ、問い合わせ導線、ワイヤーフレーム、フロントエンド実装などのWeb制作専用要素を既定値として使わないでください。
- 入力情報に基づく提案仮説として扱いながら、資料本文では営業提案らしく「〜を実施します」「〜を提案します」「〜を改善します」と記述してください。
- 入力されていない数値、実績、顧客情報、契約条件は作らないでください。不明点は「次回確認事項」として具体化してください。
- 顧客課題は、入力情報に基づく仮説として扱ってください。
- 受注確率はAランク、Bランク、Cランク、Dランクのいずれかで仮判定し、A=80%、B=60%、C=40%、D=20%を目安にprobabilityへ数値で出力してください。
- 受注確率判定では、予算、納期、課題の明確さ、自社サービスとの適合度、競合・価格比較、意思決定の見えやすさをもとに判断してください。
- 受注リスクはrisk_score 1〜5で出力し、risk_labelは「★★★☆☆」のような5段階の星表示にしてください。1が低リスク、5が高リスクです。
- 改善アクションは「決裁者確認」「予算確認」「競合ヒアリング」「納期確認」など、営業担当が次に動ける短い行動名にしてください。
- 「提案サマリー」では、提案コンセプト、解決する課題、実施範囲、期待成果を1枚で整理してください。
- 「市場・競合分析」では、案件カテゴリに合う比較軸を使ってください。Web以外でデザイン、SEO、CTAを固定軸にしないでください。
- 「概算見積」では、案件カテゴリに合う作業項目を提示してください。AI-OCRならPoC、帳票項目定義、AIモデル学習、API/CSV連携、OCR精度改善、運用支援などを使ってください。
- 「KPI設計」では、案件カテゴリに合う指標を提示してください。Web以外で問い合わせ数、CV率、自然検索流入を固定値として使わないでください。
- ヒアリング結果、自社サービス情報、成功事例データが入力されている場合は、該当カテゴリの提案方針と見積へ優先的に反映してください。
- スライドごとの箇条書きは原則3〜4個までに整理し、同じ文言を繰り返さないでください。
- 誤字脱字、論理矛盾、提案漏れ、競合との差別化、顧客課題との整合性を品質チェックしてください。
- 出力は必ず指定されたJSON構造に合わせてください。
""".strip()


def build_user_prompt(payload: ProposalRequest) -> str:
    all_text = "\n".join(
        [
            payload.project_brief,
            payload.client_company_info,
            payload.competitor_site_url,
            payload.competitor_company_name,
            payload.estimated_page_count,
            payload.cms_required,
            payload.contact_form_required,
            payload.special_function_required,
            payload.seo_required,
            payload.content_creation_required,
            payload.desired_launch_timing,
            payload.budget_range,
            payload.hearing_result,
            payload.own_service_info,
            payload.past_proposal_template,
            payload.case_studies,
        ]
    )
    profile = proposal_profile_for_text(all_text)
    structure = "\n".join(f"- {section}" for section in profile.sections)
    estimate_hint = "\n".join(f"- {line.name}: {line.priority}" for line in profile.estimate_lines[:6])
    if profile.category == "web":
        condition_lines = "\n".join(
            [
                f"- CMS有無: {payload.cms_required or '未入力'}",
                f"- 問い合わせフォーム有無: {payload.contact_form_required or '未入力'}",
                f"- 特殊機能有無: {payload.special_function_required or '未入力'}",
                f"- SEO対策有無: {payload.seo_required or '未入力'}",
                f"- 撮影・原稿作成有無: {payload.content_creation_required or '未入力'}",
            ]
        )
    else:
        condition_lines = "\n".join(
            [
                f"- 導入要件: {payload.special_function_required or payload.cms_required or '未入力'}",
                f"- 連携・入力条件: {payload.contact_form_required or '未入力'}",
                f"- 成果指標・効果測定: {payload.seo_required or '未入力'}",
                f"- 資料・データ準備: {payload.content_creation_required or '未入力'}",
            ]
        )

    return f"""
以下の情報をもとに、営業提案書の初稿を作成してください。

## 判定した案件カテゴリ
{profile.label}

## カテゴリ別の基本方針
- 提案コンセプト: {profile.concept}
- 提案概要: {profile.summary}
- 主な課題候補: {"、".join(profile.needs)}
- 主要施策候補: {"、".join(profile.strategy_items)}
- KPI候補: {"、".join(profile.kpis)}
- 見積項目候補:
{estimate_hint}

## 必須出力
1. 案件概要要約
2. 顧客課題の推定
3. 課題優先順位
4. 受注確率判定（Aランク / Bランク / Cランク / Dランク）
5. 提案方針
6. 提案ストーリー
7. 提案資料構成案
8. スライドごとの原稿
9. 想定質問と回答
10. 提案資料品質チェック結果
11. PowerPoint生成用データ

## 基本の提案資料構成
{structure}

## 入力情報の反映ルール
- 表紙: 提案先企業情報に企業名があれば反映し、未入力なら「提案先企業」とする
- 提案サマリー: 案件ごとの提案コンセプト、解決する課題、主要施策、期待成果を端的に示す
- 現状理解: 案件概要から現状、課題、機会、目指す状態を抽出し、営業ヒアリング後の整理のように記述する
- 想定される課題: 課題を優先度順に3〜4個へ絞り込む
- 市場・競合分析: カテゴリに合う比較軸を使い、現状仮説、競合標準、提案後を比較する
- ターゲット分析: 利用者、意思決定者、運用担当などカテゴリに合う対象者を整理する
- 業務フロー / カスタマージャーニー: 案件カテゴリに合う流れを示す
- 導入戦略 / Web戦略: カテゴリに合う施策、導入順序、運用改善を示す
- 導入構成 / サイトマップ: カテゴリに合う構成要素を示す
- 施策設計 / コンテンツ設計: 解決に必要な施策群を整理する
- KPI設計: カテゴリに合う効果指標を示す
- 実行方針 / 制作方針: 自社サービス情報をもとに、進め方と品質担保を示す
- 概算見積: カテゴリに合う作業項目をレンジで示す
- 予算適合判定: 予算感と概算見積レンジの差分を示し、調整方針を整理する
- 必須・推奨・オプション対応: 予算内に収めるための優先順位を分類する
- 今後の進め方: 次回確認事項、必要素材・データ、意思決定ポイント、初回打ち合わせの進め方を具体的に整理する

## 案件概要
{payload.project_brief}

## 提案先企業情報
{payload.client_company_info or "未入力"}

## 競合サイトURLまたは参考URL
{payload.competitor_site_url or "未入力"}

## 競合企業名
{payload.competitor_company_name or "未入力"}

## 見積条件
- 規模・ページ数・件数など: {payload.estimated_page_count or "未入力"}
{condition_lines}
- 希望時期: {payload.desired_launch_timing or "未入力"}
- 予算感: {payload.budget_range or "未入力"}

## ヒアリング結果
{payload.hearing_result or "未入力"}

## 自社サービス情報
{payload.own_service_info or "未入力"}

## 過去提案書テンプレート
{payload.past_proposal_template or "未入力"}

## 成功事例データ
{payload.case_studies or "未入力"}

## 出力トーン
- 入力情報に基づく提案仮説として扱いつつ、スライド本文は営業提案らしく言い切る
- 実務担当者が確認・修正しやすい
- 提案書の下書きとして使える
- 顧客への敬意が伝わる
- 不明点は「確認事項」として扱う
- 「可能性があります」「確認が必要です」「整理する必要があります」は使わない
""".strip()
