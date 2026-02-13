/**
 * Tests for /api/themes
 *
 * These tests verify the themes API endpoint behavior:
 * - Returns 401 when not authenticated
 * - Returns empty array when authenticated (database not connected)
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

describe('GET /api/themes', () => {
  beforeEach(() => {
    jest.resetModules()
    jest.clearAllMocks()
  })

  it('returns 401 when not authenticated', async () => {
    mockGetSession.mockResolvedValue(null)

    const { GET } = await import('@/app/api/themes/route')

    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(401)
    expect(data).toEqual({ error: 'Unauthorized' })
  })

  it('returns empty array when authenticated', async () => {
    mockGetSession.mockResolvedValue({
      user: { email: 'admin@example.com', name: 'Admin', image: '' },
    })

    const { GET } = await import('@/app/api/themes/route')

    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data).toEqual([])
  })
})

describe('PUT /api/themes', () => {
  beforeEach(() => {
    jest.resetModules()
    jest.clearAllMocks()
  })

  it('returns 401 when not authenticated', async () => {
    mockGetSession.mockResolvedValue(null)

    const { PUT } = await import('@/app/api/themes/route')

    const mockRequest = {
      json: async () => ({ id: 1, description: 'test' }),
    }

    const response = await PUT(mockRequest as any)
    const data = await response.json()

    expect(response.status).toBe(401)
    expect(data).toEqual({ error: 'Unauthorized' })
  })

  it('returns 503 when database not available', async () => {
    mockGetSession.mockResolvedValue({
      user: { email: 'admin@example.com', name: 'Admin', image: '' },
    })

    const { PUT } = await import('@/app/api/themes/route')

    const mockRequest = {
      json: async () => ({ id: 1, description: 'test' }),
    }

    const response = await PUT(mockRequest as any)
    const data = await response.json()

    expect(response.status).toBe(503)
    expect(data).toEqual({ error: 'Database not available' })
  })
})
