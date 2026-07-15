type ProgressProps = {
  label: string;
  value: number;
};

export function Progress({ label, value }: ProgressProps) {
  const bounded = Math.max(0, Math.min(100, value));
  return (
    <div className="pp-progress" aria-label={label} aria-valuemax={100} aria-valuemin={0} aria-valuenow={bounded} role="progressbar">
      <span>{label}</span>
      <div>
        <i style={{ width: `${bounded}%` }} />
      </div>
    </div>
  );
}
