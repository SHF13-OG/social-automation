import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AdminNav from '@/components/AdminNav'

// Mock fetch globally
const mockFetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }))
global.fetch = mockFetch as jest.Mock

// Mock useRouter
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  usePathname: () => '/admin',
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('AdminNav', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    mockPush.mockClear()
  })

  it('renders the logo with correct text', () => {
    render(<AdminNav />)

    expect(screen.getByText('2nd half faith')).toBeInTheDocument()
    expect(screen.getByText('Admin')).toBeInTheDocument()
  })

  it('renders all navigation links', () => {
    render(<AdminNav />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Themes')).toBeInTheDocument()
    expect(screen.getByText('Prayers')).toBeInTheDocument()
    expect(screen.getByText('History')).toBeInTheDocument()
    expect(screen.getByText('Schedule')).toBeInTheDocument()
    expect(screen.getByText('AI Chat')).toBeInTheDocument()
    expect(screen.getByText('Tests')).toBeInTheDocument()
  })

  it('renders View Site link', () => {
    render(<AdminNav />)

    expect(screen.getByText('View Site')).toBeInTheDocument()
  })

  it('renders Sign Out button', () => {
    render(<AdminNav />)

    expect(screen.getByText('Sign Out')).toBeInTheDocument()
  })

  it('navigation links have correct hrefs', () => {
    render(<AdminNav />)

    const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
    const themesLink = screen.getByRole('link', { name: /themes/i })
    const prayersLink = screen.getByRole('link', { name: /prayers/i })
    const historyLink = screen.getByRole('link', { name: /history/i })
    const scheduleLink = screen.getByRole('link', { name: /schedule/i })
    const chatLink = screen.getByRole('link', { name: /ai chat/i })
    const testsLink = screen.getByRole('link', { name: /tests/i })

    expect(dashboardLink).toHaveAttribute('href', '/admin')
    expect(themesLink).toHaveAttribute('href', '/admin/themes')
    expect(prayersLink).toHaveAttribute('href', '/admin/prayers')
    expect(historyLink).toHaveAttribute('href', '/admin/post-history')
    expect(scheduleLink).toHaveAttribute('href', '/admin/schedule')
    expect(chatLink).toHaveAttribute('href', '/admin/chat')
    expect(testsLink).toHaveAttribute('href', '/admin/tests')
  })

  it('View Site link points to home page', () => {
    render(<AdminNav />)

    const viewSiteLink = screen.getByRole('link', { name: /view site/i })
    expect(viewSiteLink).toHaveAttribute('href', '/')
  })

  it('calls logout API when Sign Out button is clicked', async () => {
    render(<AdminNav />)

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    fireEvent.click(signOutButton)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' })
    })

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('highlights active navigation item', () => {
    render(<AdminNav />)

    // Since usePathname is mocked to return '/admin', Dashboard should be active
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
    expect(dashboardLink).toHaveClass('bg-accent-beige/20', 'text-accent-beige')
  })
})
