import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export async function get<T>(path: string): Promise<T> {
  const { data } = await api.get<T>(path);
  return data;
}

export async function post<T>(path: string, body: unknown): Promise<T> {
  const { data } = await api.post<T>(path, body);
  return data;
}

export async function authGet<T>(path: string, token: string): Promise<T> {
  const { data } = await api.get<T>(path, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
}

export async function authPost<T>(path: string, body: unknown, token: string): Promise<T> {
  const { data } = await api.post<T>(path, body, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
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
