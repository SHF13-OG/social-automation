/**
 * Tests for GET /api/analytics
 *
 * These tests verify the analytics API endpoint behavior:
 * - Returns 401 when not authenticated
 * - Returns analytics data when authenticated
 */

// Mock the session module
const mockGetSession = jest.fn()

jest.mock('@/lib/session', () => ({
  getSession: () => mockGetSession(),
}))

jest.mock('next/server', () => ({
  NextRequest: jest.fn(),
  NextResponse: {
    json: (data: any, init?: { status?: number }) => ({
      json: async () => data,
      status: init?.status || 200,
    }),
  },
}))

describe('GET /api/analytics', () => {
  beforeEach(() => {
    jest.resetModules()
    jest.clearAllMocks()
  })

  it('returns 401 when not authenticated', async () => {
    mockGetSession.mockResolvedValue(null)

    const { GET } = await import('@/app/api/analytics/route')

    const mockRequest = {
      url: 'http://localhost:3000/api/analytics',
    }

    const response = await GET(mockRequest as any)
    const data = await response.json()

    expect(response.status).toBe(401)
    expect(data).toEqual({ error: 'Unauthorized' })
  })

  it('returns empty analytics data when authenticated (no database)', async () => {
    mockGetSession.mockResolvedValue({
      user: { email: 'admin@example.com', name: 'Admin', image: '' },
    })

    const { GET } = await import('@/app/api/analytics/route')

    const mockRequest = {
      url: 'http://localhost:3000/api/analytics',
    }

    const response = await GET(mockRequest as any)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.posts).toEqual([])
    expect(data.kpis.totalPosts).toBe(0)
    expect(data.kpis.totalViews).toBe(0)
    expect(data.recommendations).toBeDefined()
    expect(data.recommendations.length).toBeGreaterThan(0)
  })
})
