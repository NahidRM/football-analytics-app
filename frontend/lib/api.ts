const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface Match {
  match_id: string;
  label: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  date: string;
  competition: string;
  season: string;
  country: string;
  is_live: boolean;
  is_warmup: boolean;
}

export interface MatchDetail extends Match {
  fbref_available: boolean;
  available_analyses: string[];
  home_players: string[];
  away_players: string[];
}

export interface AnalyzeResponse {
  image_base64: string;
  stats_summary: string;
  match_label: string;
  fbref_available: boolean;
}

export interface ContentResponse {
  newsletter: string;
  twitter: string;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getMatches: () =>
    apiFetch<Match[]>("/matches"),

  getMatch: (matchId: string) =>
    apiFetch<MatchDetail>(`/matches/${matchId}`),

  analyze: (body: {
    match_id: string;
    team: string;
    analysis_type: string;
    player_name?: string;
  }) =>
    apiFetch<AnalyzeResponse>("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  generateContent: (body: {
    analysis_type: string;
    team: string;
    match_label: string;
    stats_summary: string;
  }) =>
    apiFetch<ContentResponse>("/content", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getCompetitions: () =>
    apiFetch<Array<{
      competition: string;
      season: string;
      country: string;
      is_live: boolean;
      is_warmup: boolean;
      match_count: number;
    }>>("/competitions"),

};
