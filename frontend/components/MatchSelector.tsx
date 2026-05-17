"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Match } from "@/lib/api";

interface Props {
  matches: Match[];
}

export default function MatchSelector({ matches }: Props) {
  const [selectedId, setSelectedId] = useState<string>("");
  const [team, setTeam] = useState<string>("");
  const router = useRouter();

  const match = matches.find((m) => m.match_id === selectedId);

  function handleAnalyze() {
    if (!match || !team) return;
    router.push(
      `/analysis/${match.match_id}?team=${encodeURIComponent(team)}`
    );
  }

  return (
    <div className="space-y-6">
      {/* Match dropdown */}
      <div>
        <label className="block text-sm text-gray-400 mb-1">Match</label>
        <select
          value={selectedId}
          onChange={(e) => {
            setSelectedId(e.target.value);
            setTeam("");
          }}
          className="w-full bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#e94560]"
        >
          <option value="">Select a match…</option>
          {matches.map((m) => (
            <option key={m.match_id} value={m.match_id}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      {/* Team picker — only shown once a match is selected */}
      {match && (
        <div>
          <label className="block text-sm text-gray-400 mb-1">
            Team to analyse
          </label>
          <div className="flex gap-3">
            {[match.home_team, match.away_team].map((t) => (
              <button
                key={t}
                onClick={() => setTeam(t)}
                className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                  team === t
                    ? "bg-[#e94560] border-[#e94560] text-white"
                    : "border-gray-700 text-gray-300 hover:border-gray-500"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* CTA */}
      <button
        onClick={handleAnalyze}
        disabled={!match || !team}
        className="w-full py-3 rounded-lg bg-[#e94560] text-white font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#c73652] transition-colors"
      >
        Open Analysis
      </button>
    </div>
  );
}
