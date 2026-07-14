"use client";

import { memo } from "react";
import { CheckCircle2 } from "lucide-react";
import type { GuidedStep, GuidedStepId } from "@/components/guided-flow/types";

type StepNavigationProps = {
  activeStep: GuidedStepId;
  completedSteps: Set<GuidedStepId>;
  isStepAvailable: (step: GuidedStepId) => boolean;
  onSelectStep: (step: GuidedStepId) => void;
  steps: GuidedStep[];
};

function StepNavigationBase({ activeStep, completedSteps, isStepAvailable, onSelectStep, steps }: StepNavigationProps) {
  return (
    <nav className="guided-step-nav" aria-label="かんたん操作フロー">
      {steps.map((step) => {
        const isActive = activeStep === step.id;
        const isCompleted = completedSteps.has(step.id);
        const isAvailable = isStepAvailable(step.id);
        return (
          <button
            aria-current={isActive ? "step" : undefined}
            className={`guided-step-pill ${isActive ? "is-active" : ""} ${isCompleted ? "is-complete" : ""}`}
            disabled={!isAvailable}
            key={step.id}
            onClick={() => onSelectStep(step.id)}
            type="button"
          >
            <span className="guided-step-number" aria-hidden="true">
              {isCompleted ? <CheckCircle2 size={16} /> : step.id}
            </span>
            <span>{step.shortLabel}</span>
          </button>
        );
      })}
    </nav>
  );
}

export const StepNavigation = memo(StepNavigationBase);
