"use client";

export function SalesInfoSection() {
  return (
    <details className="advanced-foldout">
      <summary>使い方・効果を見る</summary>
      <section className="capability-panel" aria-label="このAIでできること">
        <div className="section-heading">
          <p className="eyebrow">Value</p>
          <h2>このAIでできること</h2>
        </div>
        <div className="capability-grid">
          <article>
            <strong>提案書作成時間を短縮</strong>
            <p>案件概要から提案サマリー、課題、方針、構成案まで一気に初稿化します。</p>
          </article>
          <article>
            <strong>不足情報をAIがチェック</strong>
            <p>予算、納期、決裁者、競合、CMS、SEOなど、次回確認すべき情報を整理します。</p>
          </article>
          <article>
            <strong>PowerPoint・PDFを自動作成</strong>
            <p>詳細PPTX、要約PPTX、見積書PDFをダウンロードして、営業資料作成に使えます。</p>
          </article>
        </div>
      </section>

      <section className="before-after-panel" aria-label="Before After比較">
        <div>
          <span>導入前</span>
          <strong>手作業で2〜3時間</strong>
          <p>案件整理、構成検討、資料たたき台、見積整理を個別に作成。</p>
        </div>
        <div>
          <span>導入後</span>
          <strong>AIで20〜30分に短縮</strong>
          <p>初稿作成後、人が30分程度で確認・調整して提出準備へ。</p>
        </div>
      </section>

      <section className="usage-steps" aria-label="使い方4ステップ">
        <article>
          <span>1</span>
          <div>
            <strong>情報を貼り付ける</strong>
            <p>案件メール、議事録、チャット、Ready Crew案件情報をそのまま貼り付けます。</p>
          </div>
        </article>
        <article>
          <span>2</span>
          <div>
            <strong>AIが整理する</strong>
            <p>会社名、案件内容、目的、予算、納期、競合、CMSを自動抽出します。</p>
          </div>
        </article>
        <article>
          <span>3</span>
          <div>
            <strong>不足情報だけ回答</strong>
            <p>抽出できなかった項目だけ、AI営業アシスタントが追加で質問します。</p>
          </div>
        </article>
        <article>
          <span>4</span>
          <div>
            <strong>提案書作成</strong>
            <p>Markdown、PPTX、要約PPTX、見積書PDFを保存できます。</p>
          </div>
        </article>
      </section>
    </details>
  );
}
