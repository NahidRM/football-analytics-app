"use client";
import { Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { AnalyzeResponse, ContentResponse } from "@/lib/api";
import AnalysisCard from "@/components/AnalysisCard";
import ContentEditor from "@/components/ContentEditor";
import PendingBadge from "@/components/PendingBadge";

const ANALYSIS_LABELS: Record<string, string> = {
  passing_network: "Passing Network",
  heat_map: "Heat Map",
  shot_map: "Shot Map",
  press_map: "Press Map",
  match_stats: "Match Stats",
  player_ratings: "Player Ratings",
  xg_timeline: "xG Timeline",
};

function AnalysisPageContent({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const team = searchParams.get("team") ?? "";

  const [availableAnalyses, setAvailableAnalyses] = useState<string[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>("");
  const [playerName, setPlayerName] = useState<string>("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [content, setContent] = useState<ContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getMatch(id).then((m) => {
      setAvailableAnalyses(m.available_analyses);
      if (m.available_analyses.length > 0) setSelectedAnalysis(m.available_analyses[0]);
    }).catch(() => {});
  }, [id]);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setContent(null);
    try {
      const r = await api.analyze({
        match_id: id,
        team,
        analysis_type: selectedAnalysis,
        player_name: selectedAnalysis === "heat_map" ? playerName : undefined,
      });
      setResult(r);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateContent() {
    if (!result) return;
    setContentLoading(true);
    try {
      const c = await api.generateContent({
        analysis_type: selectedAnalysis,
        team,
        match_label: result.match_label,
        stats_summary: result.stats_summary,
      });
      setContent(c);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Content generation failed");
    } finally {
      setContentLoading(false);
    }
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <p className="text-sm text-gray-400">
          Analysing: <span className="text-white">{team}</span>
        </p>
      </div>

      {/* Analysis picker */}
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {availableAnalyses.map((a) => (
            <button
              key={a}
              onClick={() => setSelectedAnalysis(a)}
              className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                selectedAnalysis === a
                  ? "bg-[#e94560] border-[#e94560] text-white"
                  : "border-gray-700 text-gray-300 hover:border-gray-500"
              }`}
            >
              {ANALYSIS_LABELS[a] ?? a}
            </button>
          ))}
        </div>

        {selectedAnalysis === "heat_map" && (
          <input
            placeholder="Player name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm w-full max-w-xs focus:outline-none focus:border-[#e94560]"
          />
        )}

        <button
          onClick={handleAnalyze}
          disabled={loading || !selectedAnalysis}
          className="px-6 py-2 bg-[#e94560] rounded-lg text-sm font-semibold disabled:opacity-40 hover:bg-[#c73652] transition-colors"
        >
          {loading ? "Generating..." : "Generate Visualization"}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {result && (
        <div className="space-y-6">
          <AnalysisCard
            imageBase64={result.image_base64}
            analysisType={selectedAnalysis}
            team={team}
            matchLabel={result.match_label}
          />

          {!result.fbref_available && selectedAnalysis === "xg_timeline" && <PendingBadge />}

          <div>
            <p className="text-xs text-gray-400 mb-3">
              Based on: {ANALYSIS_LABELS[selectedAnalysis]} — {team} | {result.match_label}
            </p>
            <button
              onClick={handleGenerateContent}
              disabled={contentLoading}
              className="px-6 py-2 border border-[#e94560] text-[#e94560] rounded-lg text-sm font-semibold hover:bg-[#e94560] hover:text-white transition-colors disabled:opacity-40"
            >
              {contentLoading ? "Writing..." : "Generate Newsletter + Twitter Thread"}
            </button>
          </div>

          {content && (
            <ContentEditor newsletter={content.newsletter} twitter={content.twitter} />
          )}
        </div>
      )}
    </div>
  );
}

export default function AnalysisPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<div className="text-gray-400 text-sm">Loading...</div>}>
      <AnalysisPageContent id={params.id} />
    </Suspense>
  );
}
