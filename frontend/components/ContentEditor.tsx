"use client";
import { useState, useEffect } from "react";

interface Props {
  newsletter: string;
  twitter: string;
}

export default function ContentEditor({ newsletter, twitter }: Props) {
  const [nl, setNl] = useState(newsletter);
  const [tw, setTw] = useState(twitter);
  const [tab, setTab] = useState<"newsletter" | "twitter">("newsletter");

  useEffect(() => { setNl(newsletter); }, [newsletter]);
  useEffect(() => { setTw(twitter); }, [twitter]);

  return (
    <div className="space-y-3">
      <div className="flex border-b border-gray-800">
        {(["newsletter", "twitter"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm capitalize border-b-2 transition-colors -mb-px ${
              tab === t
                ? "border-[#e94560] text-white"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {t === "newsletter" ? "Newsletter Draft" : "Twitter Thread"}
          </button>
        ))}
      </div>

      {tab === "newsletter" ? (
        <textarea
          value={nl}
          onChange={(e) => setNl(e.target.value)}
          rows={14}
          className="w-full bg-[#16213e] border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-[#e94560] resize-none font-mono leading-relaxed"
        />
      ) : (
        <textarea
          value={tw}
          onChange={(e) => setTw(e.target.value)}
          rows={14}
          className="w-full bg-[#16213e] border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-[#e94560] resize-none font-mono leading-relaxed"
        />
      )}
    </div>
  );
}
