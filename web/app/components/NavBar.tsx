'use client'

import { useRouter } from 'next/navigation'
import { getToken, apiLogout } from '@/lib/auth'

export default function NavBar() {
  const router = useRouter()
  const token = getToken()

  const logout = async () => {
    if (token) await apiLogout(token)
    router.push('/login')
  }

  return (
    <nav>
      <a href="/">Dashboard</a>
      <a href="/research">Ticker Research</a>
      {token && (
        <button onClick={logout} style={{ marginLeft: 'auto' }}>
          Log out
        </button>
      )}
    </nav>
  )
}
