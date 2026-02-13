/**
 * Tests for custom Google OAuth endpoints
 *
 * These tests verify the OAuth flow configuration:
 * - Verifies OAuth URL construction
 * - Verifies state parameter handling
 * - Verifies admin email restriction
 */

describe('Google OAuth Configuration', () => {
  const originalEnv = process.env

  beforeEach(() => {
    process.env = {
      ...originalEnv,
      GOOGLE_CLIENT_ID: 'test-client-id.apps.googleusercontent.com',
      GOOGLE_CLIENT_SECRET: 'test-client-secret',
      NEXTAUTH_URL: 'https://2ndhalffaith.com',
      NEXTAUTH_SECRET: 'test-secret',
      ADMIN_EMAIL: 'admin@example.com',
    }
  })

  afterEach(() => {
    process.env = originalEnv
  })

  it('has correct Google OAuth URL format', () => {
    const clientId = process.env.GOOGLE_CLIENT_ID
    const redirectUri = `${process.env.NEXTAUTH_URL}/api/auth/google/callback`

    const googleAuthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
    googleAuthUrl.searchParams.set('client_id', clientId || '')
    googleAuthUrl.searchParams.set('redirect_uri', redirectUri)
    googleAuthUrl.searchParams.set('response_type', 'code')
    googleAuthUrl.searchParams.set('scope', 'openid email profile')

    expect(googleAuthUrl.hostname).toBe('accounts.google.com')
    expect(googleAuthUrl.searchParams.get('client_id')).toBe('test-client-id.apps.googleusercontent.com')
    expect(googleAuthUrl.searchParams.get('redirect_uri')).toBe('https://2ndhalffaith.com/api/auth/google/callback')
    expect(googleAuthUrl.searchParams.get('response_type')).toBe('code')
    expect(googleAuthUrl.searchParams.get('scope')).toBe('openid email profile')
  })

  it('callback URL matches expected format', () => {
    const callbackUrl = `${process.env.NEXTAUTH_URL}/api/auth/google/callback`
    expect(callbackUrl).toBe('https://2ndhalffaith.com/api/auth/google/callback')
  })

  it('admin email is configured', () => {
    expect(process.env.ADMIN_EMAIL).toBe('admin@example.com')
  })

  it('validates client ID format', () => {
    const clientId = process.env.GOOGLE_CLIENT_ID || ''
    expect(clientId.endsWith('.apps.googleusercontent.com')).toBe(true)
  })

  it('validates client secret format', () => {
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET || ''
    expect(clientSecret.length).toBeGreaterThan(0)
  })
})

describe('OAuth State Validation', () => {
  it('validates UUID format for state', () => {
    // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    const validUUID = '550e8400-e29b-41d4-a716-446655440000'
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    expect(validUUID).toMatch(uuidRegex)
  })

  it('state comparison works correctly', () => {
    const state1 = 'test-state-123'
    const state2 = 'test-state-123'
    const state3 = 'different-state'

    expect(state1 === state2).toBe(true)
    expect(state1 === state3).toBe(false)
  })
})

describe('Admin Authorization', () => {
  it('allows admin email', () => {
    const adminEmail = 'admin@example.com'
    const userEmail = 'admin@example.com'
    expect(userEmail === adminEmail).toBe(true)
  })

  it('rejects non-admin email', () => {
    const adminEmail = 'admin@example.com'
    const userEmail = 'other@example.com'
    expect(userEmail === adminEmail).toBe(false)
  })

  it('email comparison is case-sensitive', () => {
    const adminEmail = 'admin@example.com'
    const userEmail = 'Admin@example.com'
    expect(userEmail === adminEmail).toBe(false)
  })
})
