"use client";
import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import type { Match } from "@/lib/api";

interface Props {
  matches: Match[];
}

type Step = "competition" | "match" | "team";

const COUNTRY_FLAG: Record<string, string> = {
  "International": "🌍",
  "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "Spain": "🇪🇸",
  "Europe": "🇪🇺",
  "": "⚽",
};

export default function MatchSelector({ matches }: Props) {
  const [step, setStep] = useState<Step>("competition");
  const [selectedComp, setSelectedComp] = useState<string>("");
  const [selectedSeason, setSelectedSeason] = useState<string>("");
  const [selectedMatchId, setSelectedMatchId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [team, setTeam] = useState("");
  const router = useRouter();

  // Distinct competitions — live first, then alphabetical
  const competitions = useMemo(() => {
    const map = new Map<string, { competition: string; country: string; is_live: boolean }>();
    for (const m of matches) {
      if (!map.has(m.competition)) {
        map.set(m.competition, { competition: m.competition, country: m.country, is_live: m.is_live });
      }
    }
    return Array.from(map.values()).sort((a, b) => {
      if (a.is_live !== b.is_live) return a.is_live ? -1 : 1;
      return a.competition.localeCompare(b.competition);
    });
  }, [matches]);

  // Seasons for selected competition
  const seasons = useMemo(() => {
    if (!selectedComp) return [];
    const s = new Set(matches.filter(m => m.competition === selectedComp).map(m => m.season));
    return Array.from(s).sort().reverse();
  }, [matches, selectedComp]);

  // Matches for selected competition + season, filtered by search
  const filteredMatches = useMemo(() => {
    return matches.filter(m =>
      m.competition === selectedComp &&
      m.season === selectedSeason &&
      (search === "" || `${m.home_team} ${m.away_team}`.toLowerCase().includes(search.toLowerCase()))
    ).sort((a, b) => b.date.localeCompare(a.date));
  }, [matches, selectedComp, selectedSeason, search]);

  const selectedMatch = matches.find(m => m.match_id === selectedMatchId);

  function handleAnalyze() {
    if (!selectedMatch || !team) return;
    router.push(`/analysis/${selectedMatch.match_id}?team=${encodeURIComponent(team)}`);
  }

  function goToCompetition() {
    setStep("competition");
    setSelectedComp("");
    setSelectedSeason("");
    setSelectedMatchId("");
    setSearch("");
    setTeam("");
  }

  function handleSelectComp(compName: string) {
    setSelectedComp(compName);
    const compSeasons = Array.from(new Set(
      matches.filter(m => m.competition === compName).map(m => m.season)
    ));
    if (compSeasons.length === 1) setSelectedSeason(compSeasons[0]);
    setStep("match");
  }

  // ── COMPETITION STEP ─────────────────────────────────────────────────────────
  if (step === "competition") {
    const liveComps = competitions.filter(c => c.is_live);
    const archiveComps = competitions.filter(c => !c.is_live);

    return (
      <div className="space-y-6">
        {liveComps.length > 0 && (
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">Live</p>
            <div className="grid grid-cols-1 gap-3">
              {liveComps.map(c => (
                <button
                  key={c.competition}
                  onClick={() => handleSelectComp(c.competition)}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl border border-[#e94560] bg-[#16213e] hover:bg-[#1a2850] transition-colors text-left"
                >
                  <span className="text-2xl">{COUNTRY_FLAG[c.country] ?? "⚽"}</span>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-white">{c.competition}</p>
                  </div>
                  <span className="text-[10px] font-bold text-[#e94560] border border-[#e94560] px-1.5 py-0.5 rounded">LIVE</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {archiveComps.length > 0 && (
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">Archive</p>
            <div className="grid grid-cols-1 gap-2">
              {archiveComps.map(c => (
                <button
                  key={c.competition}
                  onClick={() => handleSelectComp(c.competition)}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-700 bg-[#16213e] hover:border-gray-500 transition-colors text-left"
                >
                  <span className="text-xl">{COUNTRY_FLAG[c.country] ?? "⚽"}</span>
                  <p className="text-sm text-gray-200">{c.competition}</p>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── MATCH STEP (season pills + match list) ────────────────────────────────────
  if (step === "match") {
    return (
      <div className="space-y-4">
        <button onClick={goToCompetition} className="text-xs text-gray-400 hover:text-gray-200">← Back</button>
        <p className="text-sm font-semibold text-white">{selectedComp}</p>

        {/* Season pills */}
        {seasons.length > 1 && (
          <div className="flex flex-wrap gap-2">
            {seasons.map(s => (
              <button
                key={s}
                onClick={() => { setSelectedSeason(s); setSearch(""); }}
                className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                  selectedSeason === s
                    ? "bg-[#e94560] border-[#e94560] text-white"
                    : "border-gray-600 text-gray-300 hover:border-gray-400"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Match list */}
        {selectedSeason && (
          <div className="space-y-2">
            <input
              placeholder="Search teams…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#e94560]"
            />
            <div className="max-h-64 overflow-y-auto space-y-1 pr-1">
              {filteredMatches.map(m => (
                <button
                  key={m.match_id}
                  onClick={() => { setSelectedMatchId(m.match_id); setTeam(""); setStep("team"); }}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-[#1a2850] transition-colors text-sm"
                >
                  <span className="text-gray-400 text-xs mr-2">{m.date.slice(0, 7)}</span>
                  <span className="text-white">{m.home_team} {m.home_score}–{m.away_score} {m.away_team}</span>
                </button>
              ))}
              {filteredMatches.length === 0 && (
                <p className="text-gray-500 text-sm px-3 py-2">No matches found.</p>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── TEAM STEP ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      <button onClick={() => setStep("match")} className="text-xs text-gray-400 hover:text-gray-200">← Back</button>

      {selectedMatch && (
        <div>
          <p className="text-sm text-gray-400 mb-1">{selectedMatch.date.slice(0, 7)}</p>
          <p className="text-base font-semibold text-white">
            {selectedMatch.home_team} {selectedMatch.home_score}–{selectedMatch.away_score} {selectedMatch.away_team}
          </p>
        </div>
      )}

      <div>
        <label className="block text-sm text-gray-400 mb-2">Team to analyse</label>
        <div className="flex gap-3">
          {[selectedMatch?.home_team, selectedMatch?.away_team].filter(Boolean).map(t => (
            <button
              key={t}
              onClick={() => setTeam(t!)}
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

      <button
        onClick={handleAnalyze}
        disabled={!team}
        className="w-full py-3 rounded-lg bg-[#e94560] text-white font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#c73652] transition-colors"
      >
        Open Analysis →
      </button>
    </div>
  );
}
