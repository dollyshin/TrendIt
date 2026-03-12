'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { apiRegister, apiLogin, setToken } from '@/lib/auth'

export default function RegisterPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await apiRegister(email, password)
      const token = await apiLogin(email, password)
      setToken(token)
      router.push('/')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container">
      <div className="card" style={{ maxWidth: '400px', margin: '4rem auto' }}>
        <h1>Create account</h1>
        {error && <p style={{ color: '#ef4444' }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '0.75rem' }}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p style={{ marginTop: '1rem' }}>
          Already have an account? <a href="/login">Sign in</a>
        </p>
      </div>
    </main>
  )
}
