'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { authGet, authPost } from '@/lib/api'
import { getToken } from '@/lib/auth'
import type { User, Portfolio, Watchlist, AnalysisRun } from '@/lib/api'

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [runs, setRuns] = useState<AnalysisRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      router.push('/login')
      return
    }
    loadDashboard(token)
  }, [])

  const loadDashboard = async (token: string) => {
    setError(null)
    try {
      const u = await authGet<User>('/users/me', token)
      setUser(u)
      const [ps, wls] = await Promise.all([
        authGet<Portfolio[]>(`/users/${u.id}/portfolios`, token).catch(() => []),
        authGet<Watchlist[]>(`/users/${u.id}/watchlists`, token).catch(() => []),
      ])
      setPortfolios(Array.isArray(ps) ? ps : [])
      setWatchlists(Array.isArray(wls) ? wls : [])
      if (Array.isArray(ps) && ps.length > 0) {
        const portfolioRuns = await authGet<AnalysisRun[]>(
          `/portfolios/${ps[0].id}/analysis-runs`,
          token
        ).catch(() => [])
        setRuns(Array.isArray(portfolioRuns) ? portfolioRuns : [])
      }
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  const token = () => getToken()!

  const createPortfolio = async () => {
    try {
      const p = await authPost<Portfolio>(
        `/users/${user!.id}/portfolios`,
        {
          name: 'Main',
          starting_cash: 10000,
        },
        token()
      )
      setPortfolios((prev) => [...prev, p])
    } catch (e) {
      setError(String(e))
    }
  }

  const createWatchlist = async () => {
    try {
      const w = await authPost<Watchlist>(
        `/users/${user!.id}/watchlists`,
        {
          name: 'Tech',
          tickers: ['AAPL', 'MSFT', 'GOOGL'],
        },
        token()
      )
      setWatchlists((prev) => [...prev, w])
    } catch (e) {
      setError(String(e))
    }
  }

  const runAnalysis = async () => {
    const portfolio = portfolios[0]
    const watchlist = watchlists[0]
    if (!portfolio || !watchlist) {
      setError('Create a portfolio and watchlist first')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const run = await authPost<AnalysisRun>(
        '/analysis-runs',
        {
          portfolio_id: portfolio.id,
          watchlist_id: watchlist.id,
        },
        token()
      )
      setRuns((prev) => [run, ...prev])
      let r = run
      while (r.status === 'queued' || r.status === 'running') {
        await new Promise((resolve) => setTimeout(resolve, 1500))
        r = await authGet<AnalysisRun>(`/analysis-runs/${run.id}`, token())
        setRuns((prev) => prev.map((x) => (x.id === run.id ? r : x)))
      }
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="container">
        <p>Loading…</p>
      </main>
    )
  }

  return (
    <main className="container">
      <h1>TrendIt Dashboard</h1>

      {error && (
        <div className="card" style={{ borderColor: '#ef4444' }}>
          {error}
        </div>
      )}

      {user && (
        <>
          <div className="card">
            <h2>User</h2>
            <p>
              {user.email} (id: {user.id})
            </p>
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
  )
}
