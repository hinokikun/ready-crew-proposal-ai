export type ProposalRequest = {
  project_brief: string;
  client_company_info: string;
  competitor_site_url: string;
  competitor_company_name: string;
  estimated_page_count: string;
  cms_required: string;
  contact_form_required: string;
  special_function_required: string;
  seo_required: string;
  content_creation_required: string;
  desired_launch_timing: string;
  budget_range: string;
  hearing_result: string;
  own_service_info: string;
  past_proposal_template: string;
  case_studies: string;
};

export type AssumedIssue = {
  issue: string;
  background: string;
  evidence: string;
  confidence: string;
};

export type IssuePriority = {
  rank: number;
  issue: string;
  reason: string;
  proposed_response: string;
};

export type WinProbability = {
  rank: "A" | "B" | "C" | "D";
  probability?: number;
  label: string;
  reason: string;
  risk_score?: number;
  risk_label?: string;
  positive_factors: string[];
  risk_factors: string[];
  recommended_next_actions: string[];
  improvement_actions?: string[];
  projected_probability_after_actions?: number;
};

export type ProposalStructureItem = {
  section: string;
  objective: string;
  key_message: string;
};

export type SlideScript = {
  slide_no: number;
  section: string;
  title: string;
  body: string[];
  speaker_notes: string;
  visual_suggestion: string;
};

export type ExpectedQuestion = {
  question: string;
  answer: string;
};

export type QualityCheck = {
  logical_consistency: string;
  typos: string;
  proposal_coverage: string;
  competitive_differentiation: string;
  alignment_with_customer_issues: string;
  human_review_notes: string;
};

export type PowerPointSlide = {
  slide_no: number;
  layout: string;
  title: string;
  bullets: string[];
  speaker_notes: string;
  visual_suggestion: string;
};

export type PowerPointData = {
  deck_title: string;
  client_name: string;
  slides: PowerPointSlide[];
};

export type ProposalAnalysis = {
  project_summary: string;
  assumed_customer_issues: AssumedIssue[];
  issue_priorities: IssuePriority[];
  win_probability: WinProbability;
  proposal_policy: string;
  proposal_story: string;
  proposal_structure: ProposalStructureItem[];
  slide_scripts: SlideScript[];
  expected_questions_and_answers: ExpectedQuestion[];
  quality_check: QualityCheck;
  powerpoint_generation_data: PowerPointData;
};

export type AnalysisResponse = {
  analysis: ProposalAnalysis;
  markdown: string;
  powerpoint_generation_data: PowerPointData;
  knowledge_insights?: KnowledgeInsights;
};

export type KnowledgeEntry = {
  id: number;
  industry: string;
  company_size: string;
  project_summary: string;
  adopted_proposal: string;
  proposal_story: string;
  adoption_reason: string;
  lost_reason: string;
  result: string;
  owner_memo: string;
  outcome: "success" | "lost" | "unknown" | string;
  rating: number;
  evaluation_status: "effective" | "needs_improvement" | string;
  tags: string;
  similarity_score?: number;
  is_high_quality?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type KnowledgeInsights = {
  similar?: {
    industry: string;
    matches: KnowledgeEntry[];
    success_patterns: string[];
    lost_patterns: string[];
    recommendation: string;
  };
  best_practices?: {
    winning_structures: string[];
    frequent_proposals: string[];
    industry_success_examples: Array<{ industry: string; count: number }>;
  };
};

