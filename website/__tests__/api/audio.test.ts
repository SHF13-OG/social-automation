/**
 * Tests for GET /api/audio/[id]
 *
 * These tests verify the audio streaming API endpoint behavior:
 * - Returns 400 for invalid prayer ID
 * - Returns 404 when audio not found
 * - Returns audio with correct content types
 * - Returns 500 on errors
 */

describe('GET /api/audio/[id]', () => {
  beforeEach(() => {
    jest.resetModules()
    jest.clearAllMocks()
  })

  it('returns 400 for invalid prayer ID', async () => {
    const mockDb = {
      prepare: jest.fn(),
    }

    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getDb: () => mockDb,
    }))
    jest.mock('fs', () => ({
      existsSync: jest.fn(),
      readFileSync: jest.fn(),
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

    const { GET } = await import('@/app/api/audio/[id]/route')

    const mockRequest = {}
    const params = Promise.resolve({ id: 'invalid' })

    const response = await GET(mockRequest as any, { params })
    const data = await response.json()

    expect(response.status).toBe(400)
    expect(data).toEqual({ error: 'Invalid prayer ID' })
  })

  it('returns 404 when audio not found in database', async () => {
    const mockStmt = {
      bind: jest.fn(),
      step: jest.fn().mockReturnValue(false),
      getAsObject: jest.fn(),
      free: jest.fn(),
    }

    const mockDb = {
      prepare: jest.fn().mockReturnValue(mockStmt),
    }

    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getDb: () => mockDb,
    }))
    jest.mock('fs', () => ({
      existsSync: jest.fn(),
      readFileSync: jest.fn(),
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

    const { GET } = await import('@/app/api/audio/[id]/route')

    const mockRequest = {}
    const params = Promise.resolve({ id: '999' })

    const response = await GET(mockRequest as any, { params })
    const data = await response.json()

    expect(response.status).toBe(404)
    expect(data).toEqual({ error: 'Audio not found' })
  })

  it('returns 404 when audio file does not exist on disk', async () => {
    const mockStmt = {
      bind: jest.fn(),
      step: jest.fn().mockReturnValue(true),
      getAsObject: jest.fn().mockReturnValue({ audio_path: 'audio/missing.mp3' }),
      free: jest.fn(),
    }

    const mockDb = {
      prepare: jest.fn().mockReturnValue(mockStmt),
    }

    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getDb: () => mockDb,
    }))
    jest.mock('fs', () => ({
      existsSync: jest.fn().mockReturnValue(false),
      readFileSync: jest.fn(),
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

    const { GET } = await import('@/app/api/audio/[id]/route')

    const mockRequest = {}
    const params = Promise.resolve({ id: '1' })

    const response = await GET(mockRequest as any, { params })
    const data = await response.json()

    expect(response.status).toBe(404)
    expect(data).toEqual({ error: 'Audio file not found' })
  })

  it('returns audio file with correct content type for mp3', async () => {
    const audioData = Buffer.from('fake audio data')

    const mockStmt = {
      bind: jest.fn(),
      step: jest.fn().mockReturnValue(true),
      getAsObject: jest.fn().mockReturnValue({ audio_path: 'audio/prayer.mp3' }),
      free: jest.fn(),
    }

    const mockDb = {
      prepare: jest.fn().mockReturnValue(mockStmt),
    }

    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getDb: () => mockDb,
    }))
    jest.mock('fs', () => ({
      existsSync: jest.fn().mockReturnValue(true),
      readFileSync: jest.fn().mockReturnValue(audioData),
    }))
    jest.mock('next/server', () => {
      class MockNextResponse {
        body: any
        headers: Map<string, string>

        constructor(body: any, init?: { headers?: Record<string, string> }) {
          this.body = body
          this.headers = new Map(Object.entries(init?.headers || {}))
        }

        get status() {
          return 200
        }
      }

      return {
        NextRequest: jest.fn(),
        NextResponse: Object.assign(MockNextResponse, {
          json: (data: any, init?: { status?: number }) => ({
            json: async () => data,
            status: init?.status || 200,
          }),
        }),
      }
    })

    const { GET } = await import('@/app/api/audio/[id]/route')

    const mockRequest = {}
    const params = Promise.resolve({ id: '1' })

    const response = await GET(mockRequest as any, { params })

    expect(response.status).toBe(200)
    expect(response.headers.get('Content-Type')).toBe('audio/mpeg')
    expect(response.headers.get('Cache-Control')).toBe('public, max-age=31536000, immutable')
  })

  it('returns 500 when database is not available', async () => {
    jest.mock('@/lib/db', () => ({
      ensureDb: jest.fn().mockResolvedValue(null),
      getDb: () => null,
    }))
    jest.mock('fs', () => ({
      existsSync: jest.fn(),
      readFileSync: jest.fn(),
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

    const { GET } = await import('@/app/api/audio/[id]/route')

    const mockRequest = {}
    const params = Promise.resolve({ id: '1' })

    const response = await GET(mockRequest as any, { params })
    const data = await response.json()

    expect(response.status).toBe(500)
    expect(data).toEqual({ error: 'Database not available' })
  })
})
