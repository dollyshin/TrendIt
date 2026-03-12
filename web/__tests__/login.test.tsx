import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, beforeEach, describe, it, expect } from 'vitest'
import LoginPage from '@/app/login/page'

const mockPush = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear()
    mockPush.mockClear()
  })

  it('renders email and password fields', () => {
    render(<LoginPage />)
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('stores token and redirects on successful login', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText(/email/i), 'user@test.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(localStorage.getItem('trendit_token')).toBe('fake-token')
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('shows error on bad credentials', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText(/email/i), 'user@test.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/LOGIN_BAD_CREDENTIALS/i)).toBeInTheDocument()
    })
    expect(mockPush).not.toHaveBeenCalled()
  })
})
