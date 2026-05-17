"use client";
import { useState } from "react";
import Link from "next/link";
import type { AnalysisRecord } from "@/lib/api";

interface Props {
  analyses: AnalysisRecord[];
}

const LABELS: Record<string, string> = {
  passing_network: "Passing Network",
  heat_map: "Heat Map",
  shot_map: "Shot Map",
  press_map: "Press Map",
  match_stats: "Match Stats",
  player_ratings: "Player Ratings",
  xg_timeline: "xG Timeline",
};

export default function HistoryList({ analyses }: Props) {
  const [filter, setFilter] = useState("");

  const filtered = filter.trim()
    ? analyses.filter((a) =>
        (a.tags ?? []).some((t) =>
          t.toLowerCase().includes(filter.toLowerCase())
        )
      )
    : analyses;

  return (
    <div className="space-y-4">
      <input
        placeholder="Filter by team..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full max-w-sm bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#e94560]"
      />

      {filtered.length === 0 ? (
        <p className="text-gray-500 text-sm">No analyses found.</p>
      ) : (
        <div className="divide-y divide-gray-800">
          {filtered.map((a) => (
            <Link
              key={a.id}
              href={`/history/${a.id}`}
              className="flex items-center justify-between py-4 hover:text-[#e94560] transition-colors group"
            >
              <div>
                <p className="text-sm font-medium">{a.match_label}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {LABELS[a.analysis_type] ?? a.analysis_type} — {a.team}
                </p>
              </div>
              <p className="text-xs text-gray-500">
                {new Date(a.created_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
