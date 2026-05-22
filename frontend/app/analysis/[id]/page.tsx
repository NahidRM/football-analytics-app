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
  const [selectedAnalyses, setSelectedAnalyses] = useState<Set<string>>(new Set());
  const [playerName, setPlayerName] = useState<string>("");
  const [results, setResults] = useState<Map<string, AnalyzeResponse>>(new Map());
  const [contents, setContents] = useState<Map<string, ContentResponse>>(new Map());
  const [loading, setLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getMatch(id).then((m) => {
      setAvailableAnalyses(m.available_analyses);
      if (m.available_analyses.length > 0) {
        setSelectedAnalyses(new Set([m.available_analyses[0]]));
      }
    }).catch((e: unknown) => {
      setError(e instanceof Error ? e.message : "Failed to load match data");
    });
  }, [id]);

  function toggleAnalysis(a: string) {
    setSelectedAnalyses(prev => {
      const next = new Set(prev);
      if (next.has(a)) next.delete(a); else next.add(a);
      return next;
    });
  }

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResults(new Map());
    setContents(new Map());
    try {
      for (const analysisType of Array.from(selectedAnalyses)) {
        const r = await api.analyze({
          match_id: id,
          team,
          analysis_type: analysisType,
          player_name: analysisType === "heat_map" ? playerName : undefined,
        });
        setResults(prev => new Map(prev).set(analysisType, r));
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateContent(analysisType: string) {
    const result = results.get(analysisType);
    if (!result) return;
    setContentLoading(analysisType);
    try {
      const c = await api.generateContent({
        analysis_type: analysisType,
        team,
        match_label: result.match_label,
        stats_summary: result.stats_summary,
        analysis_id: result.analysis_id,
      });
      setContents(prev => new Map(prev).set(analysisType, c));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Content generation failed");
    } finally {
      setContentLoading(null);
    }
  }

  const btnLabel = selectedAnalyses.size > 1
    ? `Generate ${selectedAnalyses.size} Visualizations`
    : "Generate Visualization";

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <p className="text-sm text-gray-400">
          Analysing: <span className="text-white">{team}</span>
        </p>
      </div>

      {/* Analysis picker — toggle buttons */}
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {availableAnalyses.map((a) => (
            <button
              key={a}
              onClick={() => toggleAnalysis(a)}
              className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                selectedAnalyses.has(a)
                  ? "bg-[#e94560] border-[#e94560] text-white"
                  : "border-gray-700 text-gray-300 hover:border-gray-500"
              }`}
            >
              {ANALYSIS_LABELS[a] ?? a}
            </button>
          ))}
        </div>

        {selectedAnalyses.has("heat_map") && (
          <input
            placeholder="Player name (for Heat Map)"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm w-full max-w-xs focus:outline-none focus:border-[#e94560]"
          />
        )}

        <button
          onClick={handleAnalyze}
          disabled={loading || selectedAnalyses.size === 0}
          className="px-6 py-2 bg-[#e94560] rounded-lg text-sm font-semibold disabled:opacity-40 hover:bg-[#c73652] transition-colors"
        >
          {loading ? "Generating..." : btnLabel}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {/* Results grid */}
      {results.size > 0 && (
        <div className={`grid gap-6 ${results.size > 1 ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
          {Array.from(results.entries()).map(([analysisType, result]) => {
            const content = contents.get(analysisType);
            return (
              <div key={analysisType} className="space-y-4">
                <AnalysisCard
                  imageBase64={result.image_base64}
                  analysisType={analysisType}
                  team={team}
                  matchLabel={result.match_label}
                />

                {!result.fbref_available && analysisType === "xg_timeline" && <PendingBadge />}

                <div>
                  <p className="text-xs text-gray-400 mb-2">
                    {ANALYSIS_LABELS[analysisType]} — {team}
                  </p>
                  <button
                    onClick={() => handleGenerateContent(analysisType)}
                    disabled={contentLoading === analysisType}
                    className="px-4 py-2 border border-[#e94560] text-[#e94560] rounded-lg text-sm font-semibold hover:bg-[#e94560] hover:text-white transition-colors disabled:opacity-40"
                  >
                    {contentLoading === analysisType ? "Writing..." : "Generate Content"}
                  </button>
                </div>

                {content && (
                  <ContentEditor newsletter={content.newsletter} twitter={content.twitter} />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default async function AnalysisPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <Suspense fallback={<div className="text-gray-400 text-sm">Loading...</div>}>
      <AnalysisPageContent id={id} />
    </Suspense>
  );
}
