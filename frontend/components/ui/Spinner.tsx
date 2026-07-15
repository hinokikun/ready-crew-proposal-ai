import { Loader2 } from "lucide-react";

type SpinnerProps = {
  label?: string;
};

export function Spinner({ label = "読み込み中" }: SpinnerProps) {
  return (
    <span className="pp-spinner" role="status">
      <Loader2 className="spin" size={18} aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}
