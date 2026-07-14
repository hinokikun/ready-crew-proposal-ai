"use client";

import { memo } from "react";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";

type StepFooterProps = {
  backLabel?: string;
  disabled?: boolean;
  helpText?: string;
  isLoading?: boolean;
  onBack?: () => void;
  onNext?: () => void;
  primaryLabel: string;
};

function StepFooterBase({ backLabel = "戻る", disabled = false, helpText, isLoading = false, onBack, onNext, primaryLabel }: StepFooterProps) {
  return (
    <div className="guided-step-footer">
      {onBack ? (
        <button className="guided-back-button" onClick={onBack} type="button">
          <ArrowLeft size={16} aria-hidden="true" />
          {backLabel}
        </button>
      ) : (
        <span />
      )}
      <div className="guided-footer-main">
        {helpText && <p aria-live="polite">{helpText}</p>}
        <button className="primary-button guided-next-button" disabled={disabled || isLoading} onClick={onNext} type="button">
          {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <ArrowRight size={18} aria-hidden="true" />}
          {primaryLabel}
        </button>
      </div>
    </div>
  );
}

export const StepFooter = memo(StepFooterBase);
