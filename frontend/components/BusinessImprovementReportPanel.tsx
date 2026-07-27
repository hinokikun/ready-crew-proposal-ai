"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  createBusinessImprovementDemoData,
  createBusinessImprovementReport,
  downloadBusinessImprovementReportsCsv,
  getBusinessImprovementReports,
  type BusinessImprovementReport,
  type BusinessImprovementSummary
} from "@/lib/api";

type FormState = {
  project_name: string;
  before_minutes: number;
  after_minutes: number;
  ai_input_minutes: number;
  ai_wait_minutes: number;
  revision_minutes: number;
  review_minutes: number;
  quality_score: number;
  mistake_count: number;
  comment: string;
};

type ChartKey = "reduction_rate" | "saved_minutes" | "quality_score" | "mistake_count";

const initialForm: FormState = {
  project_name: "",
  before_minutes: 60,
  after_minutes: 10,
  ai_input_minutes: 10,
  ai_wait_minutes: 10,
  revision_minutes: 10,
  review_minutes: 10,
  quality_score: 4,
  mistake_count: 0,
  comment: ""
};

function roundOne(value: number) {
  return Math.round(value * 10) / 10;
}

function formatMinutes(value: number) {
  return `${roundOne(value)}分`;
}

function formatDate(value: string) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("ja-JP");
}

function isDemoReport(item: BusinessImprovementReport) {
  return item.is_demo === true || item.is_demo === 1;
}

function escapeReportText(value: string) {
  return value.replace(/[<>]/g, (match) => (match === "<" ? "＜" : "＞")).replace(/\|/g, "｜");
}

function summarizeReports(items: BusinessImprovementReport[]): BusinessImprovementSummary {
  const totalCount = items.length;
  const totalBefore = items.reduce((total, item) => total + Number(item.before_minutes || 0), 0);
  const totalAfter = items.reduce((total, item) => total + Number(item.total_after_minutes || 0), 0);
  const totalSaved = items.reduce((total, item) => total + Number(item.saved_minutes || 0), 0);
  const totalMistakes = items.reduce((total, item) => total + Number(item.mistake_count || 0), 0);
  const averageQuality = totalCount ? roundOne(items.reduce((total, item) => total + Number(item.quality_score || 0), 0) / totalCount) : 0;
  return {
    total_count: totalCount,
    total_before_minutes: roundOne(totalBefore),
    total_after_minutes: roundOne(totalAfter),
    total_saved_minutes: roundOne(totalSaved),
    average_reduction_rate: totalBefore > 0 ? roundOne((totalSaved / totalBefore) * 100) : 0,
    average_quality: averageQuality,
    total_mistake_count: totalMistakes
  };
}

function saveBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

function buildTrainingReport(items: BusinessImprovementReport[], form: FormState) {
  const realItems = items.filter((item) => !isDemoReport(item));
  const realSummary = summarizeReports(realItems);
  if (!realItems.length) {
    return [
      "# 業務改善課題 実施結果",
      "",
      "## 1. 対象業務",
      form.project_name || "実測データ未登録",
      "",
      "## 2. 改善前の業務フロー",
      "実測データ未登録",
      "",
      "## 3. 使用したツール",
      "Ready Crew Proposal AI",
      "",
      "## 4. ツールの使用方法",
      "実測データ未登録",
      "",
      "## 5. 実施回数",
      "実測データ未登録",
      "",
      "## 6. 測定結果",
      "実測データ未登録",
      "",
      "## 7. 平均結果",
      "実測データ未登録",
      "",
      "## 8. 品質・ミスの変化",
      "実測データ未登録",
      "",
      "## 9. 今後も継続するか",
      "実測データ未登録",
      "",
      "## 10. 改善したい点",
      "実測データ未登録",
      "",
      "## 11. まとめ",
      "実測データ未登録"
    ].join("\n");
  }

  const latest = realItems[0];
  const projectName = latest?.project_name || form.project_name || "提案書作成業務";
  const beforeMinutes = latest?.before_minutes ?? form.before_minutes;
  const totalAfterMinutes = latest?.total_after_minutes ?? form.ai_input_minutes + form.ai_wait_minutes + form.revision_minutes + form.review_minutes;
  const savedMinutes = latest?.saved_minutes ?? Math.max(beforeMinutes - totalAfterMinutes, 0);
  const reductionRate = latest?.reduction_rate ?? (beforeMinutes > 0 ? roundOne((savedMinutes / beforeMinutes) * 100) : 0);
  const qualityScore = latest?.quality_score ?? form.quality_score;
  const comments = realItems
    .map((item) => item.comment)
    .filter(Boolean)
    .slice(0, 3);
  const warningLines = [
    realSummary.total_count < 3 ? "- 実施回数が3回未満です。" : "",
    realSummary.average_reduction_rate < 50 ? "- 目標の50％に達していません。" : ""
  ].filter(Boolean);
  const rows = realItems
    .map((item) =>
      [
        formatDate(item.created_at),
        escapeReportText(item.project_name || "-"),
        formatMinutes(item.before_minutes),
        formatMinutes(item.ai_input_minutes || 0),
        formatMinutes(item.ai_wait_minutes || item.after_minutes || 0),
        formatMinutes(item.review_minutes),
        formatMinutes(item.revision_minutes),
        formatMinutes(item.total_after_minutes),
        formatMinutes(item.saved_minutes),
        `${item.reduction_rate}%`,
        `${item.quality_score}/5`,
        `${item.mistake_count}件`
      ].join(" | ")
    )
    .join("\n");

  return [
    "# 業務改善課題 実施結果",
    "",
    "## 1. 対象業務",
    `${escapeReportText(projectName)}に関する提案書作成・確認・提出準備業務。`,
    "",
    "## 2. 改善前の業務フロー",
    "案件情報の整理、提案構成の作成、見積確認、提出資料の作成を手作業で行っていました。",
    "",
    "## 3. 使用したツール",
    "Ready Crew Proposal AI",
    "",
    "## 4. ツールの使用方法",
    "案件概要を入力し、AI分析、提案書生成、見積、PowerPoint、PDF、Beautiful.ai出力、業務改善レポート登録を行いました。",
    "",
    "## 5. 実施回数",
    `${realSummary.total_count}回`,
    warningLines.length ? warningLines.join("\n") : "",
    "",
    "## 6. 測定結果",
    "| 測定日 | 案件名 | 使用前時間 | AI入力時間 | AI処理待ち時間 | 確認時間 | 修正時間 | 使用後合計時間 | 短縮時間 | 短縮率 | 品質 | ミス件数 |",
    "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    rows,
    "",
    "## 7. 平均結果",
    `- 使用前の1回あたり平均時間: ${formatMinutes(realSummary.total_before_minutes / realSummary.total_count)}`,
    `- 使用後の1回あたり平均時間: ${formatMinutes(realSummary.total_after_minutes / realSummary.total_count)}`,
    `- 合計短縮時間: ${formatMinutes(realSummary.total_saved_minutes)}`,
    `- 平均短縮率: ${realSummary.average_reduction_rate}%`,
    realSummary.average_reduction_rate < 50 ? "- 目標の50％に達していません。" : "",
    "",
    "## 8. 品質・ミスの変化",
    `品質評価は5段階中${qualityScore}、ミス件数合計は${realSummary.total_mistake_count}件です。`,
    "",
    "## 9. 今後も継続するか",
    "実測結果を継続して確認し、時間短縮と品質維持の両方に効果がある場合は継続利用します。",
    "",
    "## 10. 改善したい点",
    comments.length ? comments.map((comment) => `- ${escapeReportText(comment)}`).join("\n") : "- 実測を継続し、改善したい点を追記します。",
    "",
    "## 11. まとめ",
    `直近の測定では、使用前${formatMinutes(beforeMinutes)}に対して使用後${formatMinutes(totalAfterMinutes)}、短縮時間${formatMinutes(savedMinutes)}、短縮率${reductionRate}%でした。`
  ]
    .filter(Boolean)
    .join("\n");
}

function buildPresentationSummary(items: BusinessImprovementReport[], form: FormState) {
  const realItems = items.filter((item) => !isDemoReport(item));
  if (!realItems.length) {
    return [
      "改善前は、提案書作成に〇分かかっていました。",
      "Ready Crew Proposal AIを使い、案件概要入力、AI分析、提案書生成、PPTX、PDF、Beautiful.ai出力までを確認しました。",
      "測定回数は〇回、平均短縮率は〇％、累計削減時間は〇分です。",
      "品質面では、確認や修正の時間を分けて測定できるようになりました。",
      "今後は実測件数を増やし、短縮率と品質の両方を確認しながら継続利用を判断します。"
    ].join("\n\n");
  }
  const latest = realItems[0];
  const projectName = latest?.project_name || form.project_name || "提案書作成業務";
  const realSummary = summarizeReports(realItems);
  const totalCount = realSummary.total_count;
  const averageReductionRate = realSummary.average_reduction_rate;
  const totalSavedMinutes = realSummary.total_saved_minutes;
  const averageQuality = realSummary.average_quality;
  return [
    "今回、AI営業秘書を実際の業務に近い提案書作成で利用し、作業時間の短縮効果を測定しました。",
    `対象は${projectName}です。測定件数は${totalCount}件で、平均短縮率は${averageReductionRate}%、累計削減時間は${formatMinutes(totalSavedMinutes)}でした。`,
    `品質評価の平均は5段階中${averageQuality}で、AIを使うことで初稿作成や構成整理にかかる時間を減らし、その分を確認や修正に使えるようになりました。`,
    "特に効果があったのは、案件情報から提案の骨子を作る作業、PowerPointやPDFなど提出形式へまとめる作業、そして改善結果を数値で振り返れる点です。",
    "今後は、案件ごとの測定を継続し、短縮率だけでなく品質やミス件数も合わせて確認することで、業務改善の効果をより正確に説明できるようにします。"
  ].join("\n\n");
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{note}</p>
    </article>
  );
}

function MiniChart({
  title,
  items,
  valueKey,
  unit,
  type
}: {
  title: string;
  items: BusinessImprovementReport[];
  valueKey: ChartKey;
  unit: string;
  type: "line" | "bar";
}) {
  const data = items.slice(0, 8).reverse();
  const values = data.map((item) => Number(item[valueKey] ?? 0));
  const maxValue = Math.max(...values, 1);
  const width = 320;
  const height = 140;
  const padding = 18;
  const points = values
    .map((value, index) => {
      const x = values.length === 1 ? width / 2 : padding + (index * (width - padding * 2)) / (values.length - 1);
      const y = height - padding - (value / maxValue) * (height - padding * 2);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <article className="training-chart-card">
      <div className="training-chart-heading">
        <span>{title}</span>
        <strong>{values.length ? `${roundOne(values[values.length - 1])}${unit}` : "未測定"}</strong>
      </div>
      {values.length ? (
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${title}の推移`}>
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} />
          {type === "line" ? (
            <>
              <polyline points={points} fill="none" />
              {values.map((value, index) => {
                const x = values.length === 1 ? width / 2 : padding + (index * (width - padding * 2)) / (values.length - 1);
                const y = height - padding - (value / maxValue) * (height - padding * 2);
                return <circle key={`${title}-${index}`} cx={x} cy={y} r="4" />;
              })}
            </>
          ) : (
            values.map((value, index) => {
              const barWidth = Math.max((width - padding * 2) / values.length - 10, 16);
              const x = padding + index * ((width - padding * 2) / values.length) + 5;
              const barHeight = (value / maxValue) * (height - padding * 2);
              return <rect key={`${title}-${index}`} x={x} y={height - padding - barHeight} width={barWidth} height={barHeight} rx="6" />;
            })
          )}
        </svg>
      ) : (
        <p className="empty-note">測定データを保存するとグラフが表示されます。</p>
      )}
    </article>
  );
}

export function BusinessImprovementReportPanel() {
  const panelRef = useRef<HTMLElement | null>(null);
  const [form, setForm] = useState<FormState>(initialForm);
  const [items, setItems] = useState<BusinessImprovementReport[]>([]);
  const [summary, setSummary] = useState<BusinessImprovementSummary | null>(null);
  const [includeDemo, setIncludeDemo] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState("");
  const [generatedReport, setGeneratedReport] = useState("");
  const [presentationSummary, setPresentationSummary] = useState("");
  const [screenshotMode, setScreenshotMode] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const calculated = useMemo(() => {
    const totalAfter = form.ai_input_minutes + form.ai_wait_minutes + form.revision_minutes + form.review_minutes;
    const saved = roundOne(form.before_minutes - totalAfter);
    const rate = form.before_minutes > 0 ? roundOne((saved / form.before_minutes) * 100) : 0;
    return { totalAfter, saved, rate };
  }, [form]);

  const averageSavedMinutes = summary && summary.total_count > 0 ? roundOne(summary.total_saved_minutes / summary.total_count) : 0;
  const totalMistakes = summary?.total_mistake_count ?? items.reduce((total, item) => total + Number(item.mistake_count || 0), 0);

  async function loadReports() {
    setLoading("load");
    setError("");
    try {
      const response = await getBusinessImprovementReports(includeDemo);
      const nextItems = Array.isArray(response.items) ? response.items : [];
      setItems(nextItems);
      setSummary(response.summary ?? summarizeReports(nextItems));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "業務改善レポートを取得できませんでした。");
    } finally {
      setLoading("");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (form.before_minutes <= 0) {
      setError("使用前時間は0より大きい値を入力してください。");
      return;
    }
    if ([form.ai_input_minutes, form.ai_wait_minutes, form.revision_minutes, form.review_minutes, form.mistake_count].some((value) => value < 0)) {
      setError("時間とミス件数にマイナス値は入力できません。");
      return;
    }
    if (form.quality_score < 1 || form.quality_score > 5) {
      setError("品質は1〜5で入力してください。");
      return;
    }
    if (calculated.totalAfter > 10080) {
      setError("使用後合計時間が大きすぎます。入力値を確認してください。");
      return;
    }
    setLoading("save");
    setError("");
    setMessage("");
    try {
      await createBusinessImprovementReport(form);
      setMessage("業務改善レポートを保存しました。");
      setForm(initialForm);
      await loadReports();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "業務改善レポートを保存できませんでした。");
    } finally {
      setLoading("");
    }
  }

  async function handleCsvDownload() {
    setLoading("csv");
    setError("");
    try {
      const blob = await downloadBusinessImprovementReportsCsv(includeDemo);
      saveBlob(blob, "business-improvement-report.csv");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "CSVを出力できませんでした。");
    } finally {
      setLoading("");
    }
  }

  async function handleDemoData() {
    setLoading("demo");
    setError("");
    setMessage("");
    try {
      const response = await createBusinessImprovementDemoData();
      setMessage(`サンプルデータを${response.created}件投入しました。デモデータは実測値とは別に表示されます。`);
      setIncludeDemo(true);
      await loadReports();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "サンプルデータを投入できませんでした。");
    } finally {
      setLoading("");
    }
  }

  async function copyText(text: string, label: string) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setMessage(`${label}をコピーしました。`);
    } catch {
      setError("コピーできませんでした。文章を選択して手動でコピーしてください。");
    }
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
        return;
      }
      await panelRef.current?.requestFullscreen();
    } catch {
      setError("フルスクリーン表示に切り替えできませんでした。ブラウザの設定を確認してください。");
    }
  }

  useEffect(() => {
    void loadReports();
  }, [includeDemo]);

  return (
    <section
      ref={panelRef}
      className={`system-ops-panel business-report-panel${screenshotMode ? " is-screenshot" : ""}${darkMode ? " is-dark" : ""}`}
      aria-label="業務改善ダッシュボード"
    >
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Training Dashboard</p>
          <h2>業務改善ダッシュボード</h2>
          <p>実業務での時間短縮、品質、ミス件数を研修提出用にまとめます。</p>
        </div>
        <div className="training-dashboard-actions">
          {!screenshotMode && (
            <>
              <button className="secondary-button" type="button" onClick={() => void handleCsvDownload()} disabled={loading === "csv"}>
                {loading === "csv" ? "CSV作成中" : includeDemo ? "CSV（デモ含む）" : "研修提出CSV"}
              </button>
              <button className="secondary-button" type="button" onClick={() => setGeneratedReport(buildTrainingReport(items, form))}>
                研修提出レポートを作成
              </button>
              <button className="secondary-button" type="button" onClick={() => setPresentationSummary(buildPresentationSummary(items, form))}>
                発表用サマリー作成
              </button>
              <button className="secondary-button" type="button" onClick={() => setIncludeDemo((current) => !current)} aria-pressed={includeDemo}>
                {includeDemo ? "実データのみ表示" : "デモデータも表示"}
              </button>
              <button className="secondary-button" type="button" onClick={() => void handleDemoData()} disabled={loading === "demo"}>
                {loading === "demo" ? "投入中" : "サンプルデータ投入"}
              </button>
            </>
          )}
          <button className="secondary-button" type="button" onClick={() => setScreenshotMode((current) => !current)} aria-pressed={screenshotMode}>
            {screenshotMode ? "通常表示に戻す" : "スクリーンショットモード"}
          </button>
          <button className="secondary-button" type="button" onClick={() => setDarkMode((current) => !current)} aria-pressed={darkMode}>
            {darkMode ? "ライト表示" : "ダークモード"}
          </button>
          <button className="secondary-button" type="button" onClick={() => void toggleFullscreen()}>
            フルスクリーン表示
          </button>
        </div>
      </div>

      <div className="operation-summary-grid">
        <MetricCard label="測定回数" value={`${summary?.total_count ?? 0}件`} note="保存済みの業務改善測定" />
        <MetricCard label="平均短縮率" value={`${summary?.average_reduction_rate ?? 0}%`} note="使用前時間に対する平均削減率" />
        <MetricCard label="平均短縮時間" value={formatMinutes(averageSavedMinutes)} note="1件あたりの平均削減時間" />
        <MetricCard label="累計削減時間" value={formatMinutes(summary?.total_saved_minutes ?? 0)} note="研修提出に使える合計効果" />
        <MetricCard label="品質平均" value={`${summary?.average_quality ?? 0}/5`} note="5段階評価の平均" />
        <MetricCard label="ミス件数合計" value={`${totalMistakes}件`} note="測定済みレポートの合計" />
      </div>
      <p className="status-note">
        {includeDemo
          ? "デモデータも表示中です。提出レポート本文は実データのみを対象にします。"
          : "実データのみを表示中です。デモデータは研修提出用の実測値には含めません。"}
      </p>

      <div className="training-chart-grid" aria-label="業務改善グラフ">
        <MiniChart title="短縮率推移" items={items} valueKey="reduction_rate" unit="%" type="line" />
        <MiniChart title="短縮時間" items={items} valueKey="saved_minutes" unit="分" type="bar" />
        <MiniChart title="品質推移" items={items} valueKey="quality_score" unit="/5" type="line" />
        <MiniChart title="ミス件数推移" items={items} valueKey="mistake_count" unit="件" type="bar" />
      </div>

      {!screenshotMode && (
        <form className="admin-user-form" onSubmit={handleSubmit}>
          <input
            aria-label="案件名"
            value={form.project_name}
            onChange={(event) => setForm((current) => ({ ...current, project_name: event.target.value }))}
            placeholder="案件名"
          />
          <label>
            使用前時間（分）
            <input type="number" min="0" value={form.before_minutes} onChange={(event) => setForm((current) => ({ ...current, before_minutes: Number(event.target.value) }))} />
          </label>
          <label>
            AI入力時間（分）
            <input type="number" min="0" value={form.ai_input_minutes} onChange={(event) => setForm((current) => ({ ...current, ai_input_minutes: Number(event.target.value) }))} />
          </label>
          <label>
            AI処理待ち時間（分）
            <input
              type="number"
              min="0"
              value={form.ai_wait_minutes}
              onChange={(event) =>
                setForm((current) => {
                  const value = Number(event.target.value);
                  return { ...current, ai_wait_minutes: value, after_minutes: value };
                })
              }
            />
          </label>
          <label>
            修正時間（分）
            <input type="number" min="0" value={form.revision_minutes} onChange={(event) => setForm((current) => ({ ...current, revision_minutes: Number(event.target.value) }))} />
          </label>
          <label>
            確認時間（分）
            <input type="number" min="0" value={form.review_minutes} onChange={(event) => setForm((current) => ({ ...current, review_minutes: Number(event.target.value) }))} />
          </label>
          <label>
            品質（5段階）
            <input type="number" min="1" max="5" value={form.quality_score} onChange={(event) => setForm((current) => ({ ...current, quality_score: Number(event.target.value) }))} />
          </label>
          <label>
            ミス件数
            <input type="number" min="0" value={form.mistake_count} onChange={(event) => setForm((current) => ({ ...current, mistake_count: Number(event.target.value) }))} />
          </label>
          <textarea
            aria-label="コメント"
            rows={3}
            value={form.comment}
            onChange={(event) => setForm((current) => ({ ...current, comment: event.target.value }))}
            placeholder="コメント"
          />
          <button className="primary-action" type="submit" disabled={loading === "save"}>
            {loading === "save" ? "保存中" : "レポートを保存"}
          </button>
        </form>
      )}

      <div className="operation-summary-grid training-live-calculation">
        <MetricCard label="入力中の短縮時間" value={formatMinutes(calculated.saved)} note="使用前時間 − 使用後合計時間" />
        <MetricCard label="入力中の短縮率" value={`${calculated.rate}%`} note="使用前時間との差分" />
        <MetricCard label="入力中の使用後合計" value={formatMinutes(calculated.totalAfter)} note="AI入力、AI処理待ち、確認、修正の合計" />
      </div>

      {message && <p className="status-note success">{message}</p>}
      {error && (
        <p className="status-note error" role="alert">
          {error}
        </p>
      )}

      {generatedReport && (
        <article className="training-generated-report">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Submission Text</p>
              <h3>研修提出レポート</h3>
            </div>
            {!screenshotMode && (
              <button className="secondary-button" type="button" onClick={() => void copyText(generatedReport, "研修提出レポート")}>
                レポートをコピー
              </button>
            )}
          </div>
          <pre>{generatedReport}</pre>
        </article>
      )}

      {presentationSummary && (
        <article className="training-generated-report">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Presentation Script</p>
              <h3>発表用サマリー</h3>
            </div>
            {!screenshotMode && (
              <button className="secondary-button" type="button" onClick={() => void copyText(presentationSummary, "発表用サマリー")}>
                サマリーをコピー
              </button>
            )}
          </div>
          <pre>{presentationSummary}</pre>
        </article>
      )}

      {!screenshotMode && (
        <div className="usage-dashboard-table-wrap">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>測定日</th>
                <th>案件名</th>
                <th>種別</th>
                <th>使用前</th>
                <th>AI入力</th>
                <th>AI待ち</th>
                <th>確認</th>
                <th>修正</th>
                <th>使用後合計</th>
                <th>短縮時間</th>
                <th>短縮率</th>
                <th>品質</th>
                <th>ミス件数</th>
              </tr>
            </thead>
            <tbody>
              {items.slice(0, 10).map((item) => (
                <tr key={item.id}>
                  <td>{formatDate(item.created_at)}</td>
                  <td>{item.project_name || "-"}</td>
                  <td>{isDemoReport(item) ? <span className="demo-data-badge">デモデータ</span> : "実データ"}</td>
                  <td>{formatMinutes(item.before_minutes)}</td>
                  <td>{formatMinutes(item.ai_input_minutes || 0)}</td>
                  <td>{formatMinutes(item.ai_wait_minutes || item.after_minutes || 0)}</td>
                  <td>{formatMinutes(item.review_minutes)}</td>
                  <td>{formatMinutes(item.revision_minutes)}</td>
                  <td>{formatMinutes(item.total_after_minutes)}</td>
                  <td>{formatMinutes(item.saved_minutes)}</td>
                  <td>{item.reduction_rate}%</td>
                  <td>{item.quality_score}/5</td>
                  <td>{item.mistake_count}件</td>
                </tr>
              ))}
              {!items.length && (
                <tr>
                  <td colSpan={13}>まだレポートはありません。</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
