import Link from "next/link";
import { api, type Match } from "@/lib/api";
import MatchSelector from "@/components/MatchSelector";

export default async function HomePage() {
  let matches: Match[] = [];
  try {
    matches = await api.getMatches();
  } catch {
    // backend not running — show empty state
  }

  return (
    <div className="max-w-xl space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-1">Select a match</h2>
        <p className="text-gray-400 text-sm">
          Pick a match and team to generate your analysis.
        </p>
      </div>

      {matches.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No matches available yet — make sure the backend is running on{" "}
          <code className="text-gray-400">localhost:8000</code>.
        </p>
      ) : (
        <MatchSelector matches={matches} />
      )}

      <div className="pt-4 border-t border-gray-800">
        <Link
          href="/history"
          className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
        >
          View saved analyses →
        </Link>
      </div>
    </div>
  );
}
