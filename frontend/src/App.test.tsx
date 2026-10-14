import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { LoadingSpinner } from './components/LoadingSpinner'

vi.mock('./hooks/useAuth', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    handleCallback: vi.fn(),
    isAuthenticated: false,
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}))

vi.mock('./api/client', () => ({
  api: {
    health: vi.fn().mockResolvedValue({ status: 'healthy', version: '1.0.0', demo_mode: true }),
    getCurrentUser: vi.fn().mockResolvedValue({
      id: '1',
      sub: 'test',
      email: 'test@example.com',
      name: 'Test User',
      preferred_username: 'testuser',
      roles: ['viewer'],
      created_at: new Date().toISOString(),
    }),
  },
}))

describe('App', () => {
  it('renders login page when not authenticated', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    expect(screen.getByText('lumen-console')).toBeInTheDocument()
    expect(screen.getByText('Open Agent Skills Management')).toBeInTheDocument()
    expect(screen.getByText('Redirecting to Keycloak for authentication...')).toBeInTheDocument()
  })

  it('shows spinner element on login page', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    expect(screen.getByTestId('spinner')).toBeInTheDocument()
  })
})

describe('LoadingSpinner', () => {
  it('renders with status role', () => {
    render(<LoadingSpinner />)
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading')
  })

  it('has spinner class', () => {
    render(<LoadingSpinner />)
    expect(screen.getByTestId('spinner-element')).toBeInTheDocument()
  })
})