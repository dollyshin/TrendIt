'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { get } from '@/lib/api'
import type { AnalysisRun } from '@/lib/api'
import ReactMarkdown from 'react-markdown'

export default function AnalysisPage() {
  const params = useParams()
  const id = params?.id as string
  const [run, setRun] = useState<AnalysisRun | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    get<AnalysisRun>(`/analysis-runs/${id}`)
      .then(setRun)
      .catch((e) => setError(String(e)))
  }, [id])

  if (error)
    return (
      <main className="container">
        <div className="card">{error}</div>
      </main>
    )
  if (!run)
    return (
      <main className="container">
        <p>Loading…</p>
      </main>
    )

  return (
    <main className="container">
      <p>
        <a href="/">← Dashboard</a>
      </p>
      <div className="card">
        <h1>Analysis Run #{run.id}</h1>
        <p>
          Tickers: {run.tickers.join(', ')} — Status: {run.status}
        </p>
      </div>
      {run.error && (
        <div className="card" style={{ borderColor: '#ef4444' }}>
          <strong>Error:</strong> {run.error}
        </div>
      )}
      {run.memo_markdown && (
        <div className="card markdown">
          <ReactMarkdown>{run.memo_markdown}</ReactMarkdown>
        </div>
      )}
    </main>
  )
}
