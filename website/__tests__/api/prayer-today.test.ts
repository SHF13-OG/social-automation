/**
 * Tests for GET /api/prayer/today
 *
 * These tests verify the prayer today API endpoint behavior:
 * - Returns prayer data when prayer exists
 * - Returns 404 when no prayer found
 * - Handles null audio paths
 * - Returns 500 on database errors
 */

// Mock the db module before any imports
const mockGetTodaysPrayer = jest.fn()

jest.mock('@/lib/db', () => ({
  ensureDb: jest.fn().mockResolvedValue(null),
  getTodaysPrayer: mockGetTodaysPrayer,
}))

// Mock NextResponse
jest.mock('next/server', () => ({
  NextResponse: {
    json: (data: any, init?: { status?: number }) => ({
      json: async () => data,
      status: init?.status || 200,
    }),
  },
}))

describe('GET /api/prayer/today', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns prayer data when prayer exists', async () => {
    const mockPrayer = {
      prayer_id: 1,
      prayer_text: 'Lord, grant us peace today.',
      created_at: '2024-01-15',
      verse_ref: 'John 14:27',
      verse_text: 'Peace I leave with you; my peace I give you.',
      theme_slug: 'peace',
      theme_name: 'Peace',
      tone: 'calming',
      audio_path: 'audio/prayer-1.mp3',
      duration_sec: 120,
    }

    mockGetTodaysPrayer.mockReturnValue(mockPrayer)

    // Import after mocking
    const { GET } = await import('@/app/api/prayer/today/route')
    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data).toEqual({
      prayer_id: 1,
      verse_ref: 'John 14:27',
      verse_text: 'Peace I leave with you; my peace I give you.',
      prayer_text: 'Lord, grant us peace today.',
      theme: {
        slug: 'peace',
        name: 'Peace',
        tone: 'calming',
      },
      audio_url: '/api/audio/1',
      duration_sec: 120,
      date: '2024-01-15',
    })
  })

  it('returns 404 when no prayer found', async () => {
    mockGetTodaysPrayer.mockReturnValue(undefined)

    // Reset module cache to get fresh import
    jest.resetModules()
    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getTodaysPrayer: () => undefined,
    }))
    jest.mock('next/server', () => ({
      NextResponse: {
        json: (data: any, init?: { status?: number }) => ({
          json: async () => data,
          status: init?.status || 200,
        }),
      },
    }))

    const { GET } = await import('@/app/api/prayer/today/route')
    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(404)
    expect(data).toEqual({ error: 'No prayer found for today' })
  })

  it('returns null audio_url when no audio path', async () => {
    jest.resetModules()

    const mockPrayer = {
      prayer_id: 1,
      prayer_text: 'Test prayer',
      created_at: '2024-01-15',
      verse_ref: 'John 3:16',
      verse_text: 'For God so loved the world...',
      theme_slug: 'love',
      theme_name: 'Love',
      tone: 'loving',
      audio_path: null,
      duration_sec: null,
    }

    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getTodaysPrayer: () => mockPrayer,
    }))
    jest.mock('next/server', () => ({
      NextResponse: {
        json: (data: any, init?: { status?: number }) => ({
          json: async () => data,
          status: init?.status || 200,
        }),
      },
    }))

    const { GET } = await import('@/app/api/prayer/today/route')
    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.audio_url).toBeNull()
    expect(data.duration_sec).toBeNull()
  })

  it('returns 500 on database error', async () => {
    jest.resetModules()

    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getTodaysPrayer: () => {
        throw new Error('Database connection failed')
      },
    }))
    jest.mock('next/server', () => ({
      NextResponse: {
        json: (data: any, init?: { status?: number }) => ({
          json: async () => data,
          status: init?.status || 200,
        }),
      },
    }))

    const { GET } = await import('@/app/api/prayer/today/route')
    const response = await GET()
    const data = await response.json()

    expect(response.status).toBe(500)
    expect(data).toEqual({ error: 'Failed to fetch prayer' })
  })
})
