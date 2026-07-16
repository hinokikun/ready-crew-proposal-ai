from __future__ import annotations


def architecture_nodes_for_category(category: str) -> list[str]:
    if category == "web":
        return ["流入", "情報設計", "コンテンツ", "問い合わせ", "改善"]
    if category == "image_recognition":
        return ["商品画像", "AI画像認識", "人の確認", "API/CSV連携", "商品管理システム"]
    if category == "ai_ocr":
        return ["帳票入力", "AI-OCR", "例外確認", "API/CSV連携", "運用改善"]
    if category == "rpa":
        return ["業務入力", "ロボット処理", "例外確認", "既存システム", "運用監視"]
    if category == "crm_sfa":
        return ["顧客情報", "商談管理", "活動履歴", "ダッシュボード", "改善"]
    return ["入力", "判定", "確認", "連携", "改善"]
