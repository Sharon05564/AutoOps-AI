interface StatCardProps {
  label: string;
  value: string;
  tone?: "neutral" | "danger" | "success" | "warning";
  hint?: string;
}

function StatCard({ label, value, tone = "neutral", hint }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="stat-card-label">{label}</div>
      <div className={`stat-card-value stat-card-value-${tone}`}>{value}</div>
      {hint && <div className="stat-card-hint">{hint}</div>}
    </div>
  );
}

export default StatCard;
