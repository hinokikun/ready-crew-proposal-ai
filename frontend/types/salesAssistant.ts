export type SalesAssistantStatus = {
  enabled: boolean;
  version: string;
  requires_admin: boolean;
  persistence_enabled: boolean;
  external_ai_enabled: boolean;
  proposal_preview_enabled?: boolean;
  proposal_export_enabled?: boolean;
  beautiful_ai_export_enabled?: boolean;
};

export type SalesAssistantMeetingStage =
  | "preparation"
  | "first_meeting"
  | "discovery"
  | "proposal"
  | "negotiation"
  | "closing"
  | "follow_up";

export type SalesAssistantGeneratePayload = {
  project_title: string;
  project_summary: string;
  client_name?: string;
  known_requirements: string[];
  known_constraints: string[];
  budget_information?: string;
  schedule_information?: string;
  meeting_stage: SalesAssistantMeetingStage;
  previous_interactions: string[];
  evidence_items: string[];
};

export type SalesAssistantSummary = {
  project_title: string;
  client_name: string;
  category: string;
  persona: string;
  decision_maker: string;
  strategy: string;
  story: string;
  sales_objective: string;
  recommended_positioning: string;
  primary_message: string;
  main_message: string;
  confidence: number;
  human_review_required: boolean;
  human_review_reasons: string[];
  summary_notes: string[];
};

export type SalesAssistantMeetingPlan = {
  meeting_stage: SalesAssistantMeetingStage;
  recommended_duration_minutes: number;
  objective: string;
  opening: string;
  agenda: string[];
  desired_outcome: string;
  next_step_goal: string;
  success_criteria: string[];
  time_allocation_minutes: Record<string, number>;
};

export type SalesAssistantDiscoveryQuestion = {
  id: string;
  priority: string;
  question: string;
  purpose: string;
  target_persona: string;
  required: boolean;
  follow_up_questions: string[];
  linked_strategy_field: string;
};

export type SalesAssistantTalkTrack = {
  opening_talk: string;
  problem_confirmation: string;
  proposal_explanation: string;
  value_explanation: string;
  differentiation_talk: string;
  budget_talk: string;
  schedule_talk: string;
  closing_talk: string;
  opening_message: string;
  story_beats: string[];
  transition_phrases: string[];
  closing_message: string;
};

export type SalesAssistantObjection = {
  objection_type: string;
  expected_objection: string;
  likely_objection: string;
  recommended_response: string;
  supporting_evidence: string[];
  evidence_to_prepare: string[];
  prohibited_claims: string[];
  escalation_required: boolean;
  avoid_saying: string[];
};

export type SalesAssistantDecisionSupport = {
  decision_maker: string;
  likely_decision_criteria: string[];
  approval_barriers: string[];
  information_required_for_approval: string[];
  recommended_materials: string[];
  internal_explanation_points: string[];
  decision_points: string[];
  materials_to_prepare: string[];
  approval_risks: string[];
};

export type SalesAssistantEvidenceGuidance = {
  usable_evidence: string[];
  conditional_evidence: string[];
  missing_evidence: string[];
  claims_requiring_review: string[];
  available_evidence: string[];
  evidence_gaps: string[];
  safe_claims: string[];
  claims_requiring_confirmation: string[];
};

export type SalesAssistantNextAction = {
  id: string;
  priority: string;
  owner: string;
  action: string;
  timing: string;
  completion_condition: string;
  due_hint: string;
  reason: string;
};

export type SalesAssistantFollowUp = {
  email_subject: string;
  email_body: string;
  meeting_summary_template: string;
  requested_client_actions: string[];
  internal_follow_up_actions: string[];
  subject: string;
  attachments_to_include: string[];
  confirmation_items: string[];
};

export type SalesAssistantRiskGuardrails = {
  review_severity: string;
  allowed_terms: string[];
  conditional_terms: string[];
  guardrails: string[];
  human_review_reasons: string[];
  prohibited_terms: string[];
  unsupported_claims: string[];
  compliance_notes: string[];
  removed_or_replaced_terms: string[];
};

export type SalesAssistantGenerationMetadata = {
  schema_version: string;
  generator_version: string;
  strategy_brief_version: string;
  source_strategy_schema_version: string;
  source_strategy_confidence: number;
  selected_rules: string[];
  warnings: string[];
  fallback_reasons: string[];
  deterministic: boolean;
};

export type SalesAssistantBrief = {
  summary: SalesAssistantSummary;
  meeting_plan: SalesAssistantMeetingPlan;
  discovery_questions: SalesAssistantDiscoveryQuestion[];
  talk_track: SalesAssistantTalkTrack;
  objection_handling: SalesAssistantObjection[];
  decision_maker_support: SalesAssistantDecisionSupport;
  evidence_guidance: SalesAssistantEvidenceGuidance;
  next_actions: SalesAssistantNextAction[];
  follow_up: SalesAssistantFollowUp;
  risk_and_guardrails: SalesAssistantRiskGuardrails;
  generation_metadata: SalesAssistantGenerationMetadata;
};

export type SalesAssistantGenerateResponse = {
  sales_assistant_brief: SalesAssistantBrief;
  strategy_brief?: SalesAssistantStrategyBrief;
  strategy_brief_summary: {
    category: string;
    persona: string;
    decision_maker: string;
    strategy: string;
    story: string;
    confidence: number;
  };
  warnings: string[];
  human_review_required: boolean;
  human_review_reasons: string[];
  generation_metadata: SalesAssistantGenerationMetadata;
};

export type SalesAssistantStrategyBrief = {
  schema_version: string;
  project_category: string;
  primary_persona: string;
  decision_maker: string;
  primary_strategy: string;
  story_type: string;
  primary_pack: string;
  confidence: number;
  human_review_required: boolean;
  human_review_reasons: string[];
  main_message?: string;
  kpi_pack?: string;
  estimate_pack?: string;
  priority_messages?: string[];
  risk_messages?: string[];
  required_slide_types?: string[];
};

export type SalesAssistantProposalPreviewPayload = {
  source_request: SalesAssistantGeneratePayload;
  sales_assistant_brief: SalesAssistantBrief;
  strategy_brief?: SalesAssistantStrategyBrief;
};

export type SalesAssistantProposalPreview = {
  proposal_summary: string;
  issues: Array<{
    issue: string;
    background: string;
    proposed_response: string;
    confidence: string;
  }>;
  proposal_story: string;
  proposal_policy: string;
  slide_outline: Array<{
    slide_no: number;
    title: string;
    bullets: string[];
    visual_suggestion: string;
  }>;
  kpis: string[];
  estimate_summary: string;
  deck_title: string;
  client_name: string;
  human_review_required: boolean;
  human_review_reasons: string[];
  source_versions: Record<string, string>;
};

export type SalesAssistantProposalPreviewResponse = {
  proposal_preview: SalesAssistantProposalPreview;
  proposal_response: unknown;
  human_review_required: boolean;
  human_review_reasons: string[];
  generation_metadata: {
    schema_version: string;
    proposal_generator: string;
    strategy_brief_version: string;
    sales_assistant_version: string;
    persistence_enabled: boolean;
    pptx_enabled: boolean;
    beautiful_ai_enabled: boolean;
  };
};

export type SalesAssistantExportType = "powerpoint" | "beautiful_ai";

export type SalesAssistantReviewStatus =
  | "unreviewed"
  | "reviewed"
  | "needs_revision"
  | "regenerate_recommended"
  | "approved"
  | "exportable";

export type SalesAssistantExportPayload = {
  export_type: SalesAssistantExportType;
  source_request: SalesAssistantGeneratePayload;
  sales_assistant_brief: SalesAssistantBrief;
  strategy_brief?: SalesAssistantStrategyBrief;
  proposal_preview: SalesAssistantProposalPreview;
  proposal_response: unknown;
  human_review_status: SalesAssistantReviewStatus;
  human_review_required: boolean;
  project_id?: string;
  force_new?: boolean;
};

export type SalesAssistantExportResponse = {
  export_type: SalesAssistantExportType;
  status: "success" | "failure";
  message: string;
  artifact: {
    filename?: string;
    content_type?: string;
    byte_size?: number;
    download_url?: string;
    download_method?: "POST";
    expires_on_refresh?: boolean;
    presentation_id?: string;
    editor_url?: string;
    player_url?: string;
    title?: string;
  };
  request_json_safe: Record<string, unknown>;
  response_json_safe: Record<string, unknown>;
};

export type SalesAssistantExportDownloadResult = {
  filename: string;
  byteSize: number;
  contentType: string;
};
