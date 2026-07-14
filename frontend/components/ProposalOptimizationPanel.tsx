"use client";

import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2, Sparkles } from "lucide-react";
import {
  approveProposalOptimizationItem,
  getProposalOptimizationRecommendations,
  runProposalOptimization,
  updateProposalOptimizationStatus,
  type ProposalImprovementBacklogItem,
  type ProposalOptimizationDashboard,
  type UserRole
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";

type ProposalOptimizationPanelProps = {
  projectId: string;
  currentRole?: UserRole | string;
  enabled?: boolean;
};

function canAdopt(role?: string) {
  return role === "admin" || role === "manager" || role === "member";
}

function canApprove(role?: string) {
  return role === "admin" || role === "manager";
}

function priorityClass(priority: string) {
  if (priority === "High") return "is-high";
  if (priority === "Low") return "is-low";
  return "is-medium";
}

function ProposalOptimizationPanelBase({ projectId, currentRole, enabled = true }: ProposalOptimizationPanelProps) {
  const [items, setItems] = useState<ProposalImprovementBacklogItem[]>([]);
  const [dashboard, setDashboard] = useState<ProposalOptimizationDashboard | null>(null);
  const [note, setNote] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const role = String(currentRole || "");
  const adoptAllowed = canAdopt(role);
  const approveAllowed = canApprove(role);
  const topItems = useMemo(() => items.slice(0, 5), [items]);

  const load = useCallback(async () => {
    if (!enabled || !projectId) return;
    try {
      const response = await getProposalOptimizationRecommendations(projectId);
      setItems(response.recommendations);
      setDashboard(response.dashboard);
      setNote(response.note);
    } catch {
      setItems([]);
      setDashboard(null);
    }
  }, [enabled, projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runEngine() {
    if (!projectId || !adoptAllowed) return;
    setIsLoading(true);
    setError("");
    setMessage("");
    try {
      const response = await runProposalOptimization(projectId);
      setItems(response.recommendations);
      setDashboard(response.dashboard);
      setNote(response.note);
      setMessage("Improvement backlog updated.");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}: ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function adopt(item: ProposalImprovementBacklogItem) {
    setIsLoading(true);
    setError("");
    setMessage("");
    try {
      const response = await updateProposalOptimizationStatus(item.id, "selected");
      setItems((current) => current.map((entry) => (entry.id === item.id ? response.item : entry)));
      setMessage("Improvement selected. Reflect it in the next Presentation Revision.");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}: ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function approve(item: ProposalImprovementBacklogItem) {
    setIsLoading(true);
    setError("");
    setMessage("");
    try {
      const response = await approveProposalOptimizationItem(item.id);
      setItems((current) => current.map((entry) => (entry.id === item.id ? response.item : entry)));
      setMessage("Improvement approved.");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}: ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  if (!enabled) return null;

  return (
    <section className="proposal-optimization-panel" data-testid="proposal-optimization-panel" aria-label="Proposal Optimization Engine">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Proposal Optimization Engine</p>
          <h2>Recommended improvements TOP5</h2>
          <p>
            Combines Presentation Review, Learning, Analytics, and Beautiful.ai Revision metadata to decide what should
            be improved next.
          </p>
        </div>
        <button className="secondary-button" type="button" onClick={runEngine} disabled={!adoptAllowed || isLoading}>
          {isLoading ? <Loader2 className="spin" size={16} aria-hidden="true" /> : <Sparkles size={16} aria-hidden="true" />}
          Update backlog
        </button>
      </div>

      {dashboard && (
        <div className="proposal-optimization-metrics">
          <article>
            <span>Adoption</span>
            <strong>{dashboard.improvement_adoption_rate}%</strong>
          </article>
          <article>
            <span>Revision success</span>
            <strong>{dashboard.revision_success_rate}%</strong>
          </article>
          <article>
            <span>Win-rate reference estimate</span>
            <strong>+{dashboard.predicted_win_rate_improvement}%</strong>
          </article>
          <article>
            <span>Low sample</span>
            <strong>{dashboard.insufficient_sample_count ?? 0}</strong>
          </article>
        </div>
      )}

      {note && <p className="status-note">{note}</p>}
      {message && <p className="success-note">{message}</p>}
      {error && <p className="error-note">{error}</p>}

      {topItems.length ? (
        <div className="proposal-optimization-list">
          {topItems.map((item) => (
            <article key={item.id}>
              <div>
                <span className={priorityClass(item.priority)}>{item.priority}</span>
                <strong>{item.title}</strong>
                <small>
                  Score {item.composite_score} / Confidence {Math.round(item.confidence * 100)}% / Sample {item.sample_size ?? item.simulation?.sample_size ?? 0}
                </small>
              </div>
              <p>{item.explanation || item.summary}</p>
              <p className="status-note">
                Evidence: {item.evidence_type || item.simulation?.evidence_type || "insufficient_data"} / AI reference estimate, not a guaranteed result.
                {item.requires_human_review ? " Human review required." : ""}
              </p>
              <dl>
                <div>
                  <dt>Reference estimate</dt>
                  <dd>Win rate +{item.simulation?.win_rate_delta ?? item.predicted_win_rate_delta}%</dd>
                </div>
                <div>
                  <dt>Review count</dt>
                  <dd>{item.simulation?.review_count_delta ?? 0}%</dd>
                </div>
                <div>
                  <dt>Effort</dt>
                  <dd>{item.effort}/5</dd>
                </div>
              </dl>
              <div className="proposal-optimization-actions">
                <button
                  className="primary-button"
                  type="button"
                  onClick={() => adopt(item)}
                  disabled={!adoptAllowed || isLoading || item.status === "selected" || item.status === "approved" || item.status === "in_revision"}
                >
                  <CheckCircle2 size={16} aria-hidden="true" />
                  {item.status === "selected" || item.status === "approved" || item.status === "in_revision" ? "Selected" : "Select"}
                </button>
                {approveAllowed && (
                  <button className="secondary-button" type="button" onClick={() => approve(item)} disabled={isLoading || item.status === "approved"}>
                    Approve
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="status-note">No improvement backlog yet. Create a proposal, then update the backlog.</p>
      )}
    </section>
  );
}

export const ProposalOptimizationPanel = memo(ProposalOptimizationPanelBase);
