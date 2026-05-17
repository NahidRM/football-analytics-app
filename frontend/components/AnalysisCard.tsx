"use client";

interface Props {
  imageBase64: string;
  analysisType: string;
  team: string;
  matchLabel: string;
}

export default function AnalysisCard({ imageBase64, analysisType, team, matchLabel }: Props) {
  function handleDownload() {
    const a = document.createElement("a");
    a.href = `data:image/png;base64,${imageBase64}`;
    a.download = `${team.replace(/\s+/g, "_").toLowerCase()}_${analysisType}.png`;
    a.click();
  }

  return (
    <div className="space-y-3">
      <img
        src={`data:image/png;base64,${imageBase64}`}
        alt={`${analysisType} for ${team}`}
        className="w-full rounded-lg border border-gray-800"
      />
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>{analysisType.replace(/_/g, " ")} — {team} | {matchLabel}</span>
        <button
          onClick={handleDownload}
          className="px-3 py-1 border border-gray-700 rounded hover:border-gray-400 transition-colors"
        >
          ↓ Download
        </button>
      </div>
    </div>
  );
}
