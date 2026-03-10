const API = '/api';

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type User = { id: number; email: string };
export type Portfolio = { id: number; user_id: number; name: string; starting_cash: number; cash: number };
export type Watchlist = { id: number; user_id: number; name: string; tickers: string[] };
export type AnalysisRun = {
  id: number;
  portfolio_id: number;
  status: string;
  tickers: string[];
  memo_markdown?: string | null;
  error?: string | null;
};
export type TickerResearch = { ticker: string; report_markdown: string };
