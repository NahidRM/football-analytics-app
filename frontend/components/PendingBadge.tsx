export default function PendingBadge() {
  return (
    <div className="inline-flex items-center gap-2 bg-yellow-900/30 border border-yellow-700/50 text-yellow-400 text-xs px-3 py-1.5 rounded-full">
      <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
      Shot data and xG timeline available in a few hours — refresh to check.
    </div>
  );
}
