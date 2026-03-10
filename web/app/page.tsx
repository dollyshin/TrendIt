'use client';

import { useState, useEffect } from 'react';
import { get, post } from '@/lib/api';
import type { User, Portfolio, Watchlist, AnalysisRun } from '@/lib/api';

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [email, setEmail] = useState('demo@trendit.local');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initUser = async () => {
    setLoading(true);
    setError(null);
    try {
      const u = await post<User>('/users', { email });
      setUser(u);
      const [ps, wls] = await Promise.all([
        get<Portfolio[]>(`/users/${u.id}/portfolios`).catch(() => []),
        get<Watchlist[]>(`/users/${u.id}/watchlists`).catch(() => []),
      ]);
      setPortfolios(Array.isArray(ps) ? ps : []);
      setWatchlists(Array.isArray(wls) ? wls : []);
      if (Array.isArray(ps) && ps.length > 0) {
        const portfolioRuns = await get<AnalysisRun[]>(`/portfolios/${ps[0].id}/analysis-runs`).catch(() => []);
        setRuns(Array.isArray(portfolioRuns) ? portfolioRuns : []);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    get<{ ok: boolean }>('/health').catch(() => setError('API unreachable'));
  }, []);

  const createPortfolio = async () => {
    if (!user) return;
    try {
      const p = await post<Portfolio>('/users/' + user.id + '/portfolios', {
        name: 'Main',
        starting_cash: 10000,
      });
      setPortfolios((prev) => [...prev, p]);
    } catch (e) {
      setError(String(e));
    }
  };

  const createWatchlist = async () => {
    if (!user) return;
    try {
      const w = await post<Watchlist>('/users/' + user.id + '/watchlists', {
        name: 'Tech',
        tickers: ['AAPL', 'MSFT', 'GOOGL'],
      });
      setWatchlists((prev) => [...prev, w]);
    } catch (e) {
      setError(String(e));
    }
  };

  const runAnalysis = async () => {
    const portfolio = portfolios[0];
    const watchlist = watchlists[0];
    if (!portfolio || !watchlist) {
      setError('Create a portfolio and watchlist first');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const run = await post<AnalysisRun>('/analysis-runs', {
        portfolio_id: portfolio.id,
        watchlist_id: watchlist.id,
      });
      setRuns((prev) => [run, ...prev]);
      // Poll until done
      let r = run;
      while (r.status === 'queued' || r.status === 'running') {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        r = await get<AnalysisRun>(`/analysis-runs/${run.id}`);
        setRuns((prev) => prev.map((x) => (x.id === run.id ? r : x)));
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <h1>TrendIt Dashboard</h1>

      {error && (
        <div className="card" style={{ borderColor: '#ef4444' }}>
          {error}
        </div>
      )}

      {!user ? (
        <div className="card">
          <h2>Get started</h2>
          <p>Create a user to manage portfolios and run analysis.</p>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
          />
          <button className="btn" onClick={initUser} disabled={loading} style={{ marginLeft: '0.5rem' }}>
            Create user
          </button>
        </div>
      ) : (
        <>
          <div className="card">
            <h2>User</h2>
            <p>{user.email} (id: {user.id})</p>
          </div>

          <div className="card">
            <h2>Portfolios</h2>
            {portfolios.length === 0 ? (
              <button className="btn" onClick={createPortfolio}>
                Create portfolio
              </button>
            ) : (
              <ul>
                {portfolios.map((p) => (
                  <li key={p.id}>
                    {p.name} — cash: ${p.cash.toLocaleString()}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card">
            <h2>Watchlists</h2>
            {watchlists.length === 0 ? (
              <button className="btn" onClick={createWatchlist}>
                Create watchlist (AAPL, MSFT, GOOGL)
              </button>
            ) : (
              <ul>
                {watchlists.map((w) => (
                  <li key={w.id}>
                    {w.name}: {w.tickers.join(', ')}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card">
            <h2>Run analysis</h2>
            <p>Generate a daily memo for your watchlist (manual trigger).</p>
            <button
              className="btn"
              onClick={runAnalysis}
              disabled={loading || portfolios.length === 0 || watchlists.length === 0}
            >
              {loading ? 'Running…' : 'Run analysis'}
            </button>
          </div>

          {runs.length > 0 && (
            <div className="card">
              <h2>Recent analysis runs</h2>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {runs.map((r) => (
                  <li key={r.id} style={{ marginBottom: '0.5rem' }}>
                    <a href={`/analysis/${r.id}`}>
                      Run #{r.id} — {r.tickers.join(', ')} — {r.status}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </main>
  );
}
