/**
 * Tests for /api/queue
 *
 * These tests verify the queue API endpoint behavior:
 * - Returns 401 when not authenticated
 * - Returns empty array when authenticated
 */

// Mock the session module
const mockGetSession = jest.fn()

jest.mock('@/lib/session', () => ({
  getSession: () => mockGetSession(),
}))

const mockGetQueueItems = jest.fn()

jest.mock('@/lib/db', () => ({
  ensureDb: jest.fn(),
  getQueueItems: (...args: any[]) => mockGetQueueItems(...args),
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

describe('GET /api/queue', () => {
  beforeEach(() => {
    jest.resetModules()
    jest.clearAllMocks()
  })

  it('returns 401 when not authenticated', async () => {
    mockGetSession.mockResolvedValue(null)

    const { GET } = await import('@/app/api/queue/route')

    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(401)
    expect(data).toEqual({ error: 'Unauthorized' })
  })

  it('returns empty array when authenticated', async () => {
    mockGetSession.mockResolvedValue({
      user: { email: 'admin@example.com', name: 'Admin', image: '' },
    })
    mockGetQueueItems.mockReturnValue([])

    const { GET } = await import('@/app/api/queue/route')

    const mockRequest = { url: 'http://localhost/api/queue' }
    const response = await GET(mockRequest as any)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data).toEqual([])
  })
})
