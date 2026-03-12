'use client'

import { useState } from 'react'
import { post } from '@/lib/api'
import type { TickerResearch } from '@/lib/api'
import ReactMarkdown from 'react-markdown'

export default function ResearchPage() {
  const [ticker, setTicker] = useState('')
  const [report, setReport] = useState<TickerResearch | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runResearch = async () => {
    const sym = ticker.trim().toUpperCase()
    if (!sym) {
      setError('Enter a ticker symbol')
      return
    }
    setLoading(true)
    setError(null)
    setReport(null)
    try {
      const r = await post<TickerResearch>('/ticker-research', { ticker: sym })
      setReport(r)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container">
      <h1>Ticker Research</h1>
      <p>
        On-demand deep-dive analysis for a single stock. Uses price data and AI (when LLM is
        configured).
      </p>

      <div className="card">
        <label>
          Ticker symbol:{' '}
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="e.g. AAPL"
            maxLength={10}
            style={{ width: '8rem' }}
          />
        </label>
        <button
          className="btn"
          onClick={runResearch}
          disabled={loading}
          style={{ marginLeft: '0.5rem' }}
        >
          {loading ? 'Analyzing…' : 'Run research'}
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor: '#ef4444' }}>
          {error}
        </div>
      )}

      {report && (
        <div className="card markdown">
          <ReactMarkdown>{report.report_markdown}</ReactMarkdown>
        </div>
      )}
    </main>
  )
}
