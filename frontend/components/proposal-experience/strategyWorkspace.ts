import type {
  ProposalStrategyWorkspace,
  SalesStrategyBrief,
  SalesStrategyObjection,
  StoryCandidate,
  StrategyScoreItem,
  StrategyWorkspaceChange,
  StrategyWorkspaceEditableField,
  StrategyWorkspaceScore,
  ToneCandidate
} from "@/components/proposal-experience/types";

const editableFields: StrategyWorkspaceEditableField[] = [
  "winningStrategy",
  "proposalPosition",
  "decisionMaker",
  "competitiveSituation",
  "expectedObjections",
  "recommendedPresentationTone",
  "businessGoal",
  "painPoints",
  "differentiation",
  "recommendedStoryType",
  "recommendedSlideTypes",
  "executiveSummary"
];

export const toneCandidates: ToneCandidate[] = [
  { id: "tone-executive", label: "Executive", tone: "Executive", summary: "Board-ready, ROI first, low detail density." },
  { id: "tone-consulting", label: "Consulting", tone: "Consulting", summary: "Structured issue, evidence, and recommendation flow." },
  { id: "tone-agency", label: "Agency", tone: "Agency", summary: "Customer experience, creative impact, and differentiation." },
  { id: "tone-data", label: "Data Driven", tone: "Data Driven", summary: "KPI, comparison criteria, and measurable value." }
];

export function createProposalStrategyWorkspace(brief: SalesStrategyBrief): ProposalStrategyWorkspace {
  const aiBrief = cloneBrief(brief);
  const editedBrief = cloneBrief(brief);
  return {
    schemaVersion: "proposal_strategy_workspace_v1",
    status: "draft",
    aiBrief,
    editedBrief,
    selectedStoryId: storyIdFor(editedBrief.recommendedStoryType),
    selectedTone: editedBrief.recommendedPresentationTone,
    confirmedInformation: [],
    changes: compareStrategyBriefs(aiBrief, editedBrief)
  };
}

export function updateWorkspaceField(
  workspace: ProposalStrategyWorkspace,
  field: StrategyWorkspaceEditableField,
  value: string
): ProposalStrategyWorkspace {
  const editedBrief = cloneBrief(workspace.editedBrief);
  applyFieldValue(editedBrief, field, value);
  return rebuildWorkspace(workspace, editedBrief, "review");
}

export function selectWorkspaceStory(
  workspace: ProposalStrategyWorkspace,
  candidate: StoryCandidate
): ProposalStrategyWorkspace {
  const editedBrief = {
    ...cloneBrief(workspace.editedBrief),
    recommendedStoryType: candidate.storyType,
    recommendedSlideTypes: [...candidate.slideTypes]
  };
  return {
    ...rebuildWorkspace(workspace, editedBrief, "review"),
    selectedStoryId: candidate.id
  };
}

export function selectWorkspaceTone(workspace: ProposalStrategyWorkspace, tone: string): ProposalStrategyWorkspace {
  const editedBrief = {
    ...cloneBrief(workspace.editedBrief),
    recommendedPresentationTone: tone
  };
  return {
    ...rebuildWorkspace(workspace, editedBrief, "review"),
    selectedTone: tone
  };
}

export function confirmWorkspaceInformation(workspace: ProposalStrategyWorkspace, item: string): ProposalStrategyWorkspace {
  const confirmedInformation = workspace.confirmedInformation.includes(item)
    ? workspace.confirmedInformation
    : [...workspace.confirmedInformation, item];
  const editedBrief = cloneBrief(workspace.editedBrief);
  editedBrief.riskFactors = editedBrief.riskFactors.map((risk) =>
    risk.item === item ? { ...risk, category: "provided", reason: "Confirmed by sales." } : risk
  );
  return {
    ...rebuildWorkspace(workspace, editedBrief, "review"),
    confirmedInformation
  };
}

export function resetWorkspace(workspace: ProposalStrategyWorkspace): ProposalStrategyWorkspace {
  return createProposalStrategyWorkspace(workspace.aiBrief);
}

export function approveWorkspace(workspace: ProposalStrategyWorkspace): ProposalStrategyWorkspace {
  return rebuildWorkspace(workspace, workspace.editedBrief, "approved");
}

export function compareStrategyBriefs(aiBrief: SalesStrategyBrief, editedBrief: SalesStrategyBrief): StrategyWorkspaceChange[] {
  return editableFields.map((field) => {
    const aiValue = fieldToText(aiBrief, field);
    const editedValue = fieldToText(editedBrief, field);
    return {
      field,
      aiValue,
      editedValue,
      changed: aiValue !== editedValue
    };
  });
}

export function evaluateStrategyWorkspace(workspace: ProposalStrategyWorkspace): StrategyWorkspaceScore {
  const brief = workspace.editedBrief;
  const changedFieldCount = workspace.changes.filter((change) => change.changed).length;
  const confirmedInformationCount = workspace.confirmedInformation.length;
  const missingCount = brief.evidenceClassification.missing.length + brief.evidenceClassification.needsConfirmation.length;
  const objectionCount = brief.expectedObjections.length;
  const differentiationCount = brief.differentiation.length;
  const riskCoverage = brief.riskFactors.filter((risk) => risk.category !== "missing").length;
  const executiveFit = brief.recommendedPresentationTone === "Executive" || brief.decisionMaker === "executive" ? 92 : 76;
  const fieldFit = brief.decisionMaker === "field_leader" || brief.riskFactors.some((risk) => /operation|field|現場/.test(risk.item)) ? 88 : 74;
  const items: StrategyScoreItem[] = [
    scoreItem("customer_understanding", "顧客理解", 86 - missingCount * 5 + confirmedInformationCount * 3, "Missing facts reduce customer understanding."),
    scoreItem("competitive_advantage", "競争優位性", 72 + differentiationCount * 6 + (brief.competitiveSituation ? 4 : 0), "Differentiation and competition framing are scored."),
    scoreItem("persuasiveness", "説得力", 74 + objectionCount * 4 + changedFieldCount * 2, "Objections and human edits improve persuasion."),
    scoreItem("roi_appeal", "ROI訴求", /roi|cost|削減|売上|profit|kpi/i.test(`${brief.winningStrategy} ${brief.businessGoal}`) ? 90 : 70, "ROI terms and measurable goals are checked."),
    scoreItem("risk_coverage", "リスク対応", 66 + riskCoverage * 5, "Provided and confirmed risks raise readiness."),
    scoreItem("story_consistency", "ストーリー一貫性", brief.recommendedSlideTypes.length >= 6 ? 88 : 70, "A complete slide sequence improves story consistency."),
    scoreItem("executive_fit", "経営層向け適合", executiveFit, "Executive tone and decision maker alignment are checked."),
    scoreItem("field_fit", "現場向け適合", fieldFit, "Operational burden and field confirmation are checked.")
  ];
  return {
    total: clamp(Math.round(items.reduce((sum, item) => sum + item.score, 0) / items.length)),
    items,
    changedFieldCount,
    confirmedInformationCount
  };
}

export function buildStoryCandidates(brief: SalesStrategyBrief): StoryCandidate[] {
  const baseSlides = brief.recommendedSlideTypes.length
    ? brief.recommendedSlideTypes
    : ["Cover", "Problem", "Proposal", "KPI", "Estimate", "Next Action"];
  const candidates: StoryCandidate[] = [
    {
      id: storyIdFor(brief.recommendedStoryType),
      label: `A: ${brief.recommendedStoryType}`,
      storyType: brief.recommendedStoryType,
      reason: "Use the AI-recommended story based on current strategy.",
      slideTypes: baseSlides
    },
    {
      id: "story-roi",
      label: "B: ROI",
      storyType: "ROI",
      reason: "Lead with business impact, investment logic, and measurable value.",
      slideTypes: unique(["Cover", "Executive Summary", "Problem", "KPI", "Estimate", "Risk", "Next Action", ...baseSlides]).slice(0, 9)
    },
    {
      id: brief.competitiveSituation.includes("未") ? "story-dx" : "story-competitive",
      label: brief.competitiveSituation.includes("未") ? "C: DX" : "C: Competitive",
      storyType: brief.competitiveSituation.includes("未") ? "DX" : "Competitive Differentiation",
      reason: brief.competitiveSituation.includes("未")
        ? "Frame the proposal as operational transformation."
        : "Make differentiation and selection criteria clear before estimate.",
      slideTypes: unique(["Cover", "Problem", "Comparison", "Proposal", "Roadmap", "KPI", "Estimate", "Next Action", ...baseSlides]).slice(0, 9)
    }
  ];
  return uniqueBy(candidates, (candidate) => candidate.storyType).slice(0, 3);
}

export function fieldToText(brief: SalesStrategyBrief, field: StrategyWorkspaceEditableField): string {
  if (field === "expectedObjections") {
    return brief.expectedObjections.map((item) => item.objection).join("\n");
  }
  if (field === "painPoints") return brief.painPoints.join("\n");
  if (field === "differentiation") return brief.differentiation.join("\n");
  if (field === "recommendedSlideTypes") return brief.recommendedSlideTypes.join("\n");
  const value = brief[field];
  return typeof value === "string" ? value : "";
}

function rebuildWorkspace(
  workspace: ProposalStrategyWorkspace,
  editedBrief: SalesStrategyBrief,
  status: ProposalStrategyWorkspace["status"]
): ProposalStrategyWorkspace {
  return {
    ...workspace,
    status,
    editedBrief,
    selectedStoryId: storyIdFor(editedBrief.recommendedStoryType),
    selectedTone: editedBrief.recommendedPresentationTone,
    changes: compareStrategyBriefs(workspace.aiBrief, editedBrief)
  };
}

function applyFieldValue(brief: SalesStrategyBrief, field: StrategyWorkspaceEditableField, value: string): void {
  if (field === "expectedObjections") {
    brief.expectedObjections = parseObjections(value, brief.expectedObjections);
    return;
  }
  if (field === "painPoints") {
    brief.painPoints = splitLines(value);
    return;
  }
  if (field === "differentiation") {
    brief.differentiation = splitLines(value);
    return;
  }
  if (field === "recommendedSlideTypes") {
    brief.recommendedSlideTypes = splitLines(value);
    return;
  }
  (brief as unknown as Record<string, string>)[field] = value;
}

function parseObjections(value: string, previous: SalesStrategyObjection[]): SalesStrategyObjection[] {
  return splitLines(value).map((line, index) => {
    const existing = previous[index];
    return {
      objection: line,
      reason: existing?.reason || "Sales edited objection.",
      recommendedSlide: existing?.recommendedSlide || "Risk",
      recommendedEvidence: existing?.recommendedEvidence || "Evidence to be confirmed"
    };
  });
}

function scoreItem(key: string, label: string, score: number, reason: string): StrategyScoreItem {
  return { key, label, score: clamp(score), reason };
}

function storyIdFor(storyType: string): string {
  return `story-${storyType.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "default"}`;
}

function splitLines(value: string): string[] {
  return value
    .split(/\n|,|、|・/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function cloneBrief(brief: SalesStrategyBrief): SalesStrategyBrief {
  return JSON.parse(JSON.stringify(brief)) as SalesStrategyBrief;
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function unique(values: string[]): string[] {
  return values.filter((value, index) => values.indexOf(value) === index);
}

function uniqueBy<T>(values: T[], key: (value: T) => string): T[] {
  const seen = new Set<string>();
  return values.filter((value) => {
    const next = key(value);
    if (seen.has(next)) return false;
    seen.add(next);
    return true;
  });
}
