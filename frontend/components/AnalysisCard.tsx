"use client";
import { useState } from "react";

interface Props {
  imageBase64: string;
  analysisType: string;
  team: string;
  matchLabel: string;
}

export default function AnalysisCard({ imageBase64, analysisType, team, matchLabel }: Props) {
  const [enlarged, setEnlarged] = useState(false);
  const src = `data:image/png;base64,${imageBase64}`;

  function handleDownload() {
    const a = document.createElement("a");
    a.href = src;
    a.download = `${team.replace(/\s+/g, "_").toLowerCase()}_${analysisType}.png`;
    a.click();
  }

  return (
    <>
      <div className="space-y-3">
        <img
          src={src}
          alt={`${analysisType} for ${team}`}
          className="w-full rounded-lg border border-gray-800 cursor-zoom-in"
          onClick={() => setEnlarged(true)}
          title="Click to enlarge"
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

      {/* Fullscreen overlay — click anywhere to close */}
      {enlarged && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-6 cursor-zoom-out"
          onClick={() => setEnlarged(false)}
        >
          <img
            src={src}
            alt={`${analysisType} for ${team}`}
            className="max-w-full max-h-full rounded-lg shadow-2xl"
          />
          <button
            className="absolute top-4 right-4 text-white text-2xl font-bold hover:text-gray-300"
            onClick={() => setEnlarged(false)}
          >
            ✕
          </button>
        </div>
      )}
    </>
  );
}
