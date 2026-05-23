"use client";

import { useState, useEffect } from "react";
import { api, type Match } from "@/lib/api";
import MatchSelector from "@/components/MatchSelector";

export default function HomeContent() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getMatches()
      .then(setMatches)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-xl space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-1">Select a match</h2>
        <p className="text-gray-400 text-sm">
          Pick a match and team to generate your analysis.
        </p>
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Loading matches…</p>
      ) : matches.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No matches available — the backend may still be starting up. Try
          refreshing in a moment.
        </p>
      ) : (
        <MatchSelector matches={matches} />
      )}
    </div>
  );
}
