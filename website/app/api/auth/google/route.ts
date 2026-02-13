import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export const dynamic = 'force-dynamic'

export async function GET() {
  const clientId = process.env.GOOGLE_CLIENT_ID
  const redirectUri = `${process.env.NEXTAUTH_URL}/api/auth/google/callback`

  // Generate a random state for CSRF protection
  const state = crypto.randomUUID()

  // Store state in cookie
  const cookieStore = await cookies()
  cookieStore.set('oauth_state', state, {
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    maxAge: 60 * 10, // 10 minutes
    path: '/',
  })

  // Construct Google OAuth URL
  const googleAuthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
  googleAuthUrl.searchParams.set('client_id', clientId || '')
  googleAuthUrl.searchParams.set('redirect_uri', redirectUri)
  googleAuthUrl.searchParams.set('response_type', 'code')
  googleAuthUrl.searchParams.set('scope', 'openid email profile')
  googleAuthUrl.searchParams.set('access_type', 'offline')
  googleAuthUrl.searchParams.set('prompt', 'consent')
  googleAuthUrl.searchParams.set('state', state)

  return NextResponse.redirect(googleAuthUrl.toString())
}
