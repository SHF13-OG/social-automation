import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { SignJWT } from 'jose'

export const dynamic = 'force-dynamic'

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'secondhalf.faith.media@gmail.com'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const code = searchParams.get('code')
  const state = searchParams.get('state')
  const error = searchParams.get('error')

  if (error) {
    return NextResponse.redirect(new URL(`/login?error=${error}`, process.env.NEXTAUTH_URL))
  }

  // Verify state
  const cookieStore = await cookies()
  const storedState = cookieStore.get('oauth_state')?.value

  if (!state || state !== storedState) {
    return NextResponse.redirect(new URL('/login?error=invalid_state', process.env.NEXTAUTH_URL))
  }

  // Clear state cookie
  cookieStore.delete('oauth_state')

  if (!code) {
    return NextResponse.redirect(new URL('/login?error=no_code', process.env.NEXTAUTH_URL))
  }

  try {
    // Exchange code for tokens
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: process.env.GOOGLE_CLIENT_ID || '',
        client_secret: process.env.GOOGLE_CLIENT_SECRET || '',
        code,
        grant_type: 'authorization_code',
        redirect_uri: `${process.env.NEXTAUTH_URL}/api/auth/google/callback`,
      }),
    })

    if (!tokenResponse.ok) {
      const errorData = await tokenResponse.text()
      console.error('Token exchange failed:', errorData)
      return NextResponse.redirect(new URL('/login?error=token_exchange', process.env.NEXTAUTH_URL))
    }

    const tokens = await tokenResponse.json()

    // Get user info
    const userResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${tokens.access_token}`,
      },
    })

    if (!userResponse.ok) {
      return NextResponse.redirect(new URL('/login?error=user_info', process.env.NEXTAUTH_URL))
    }

    const user = await userResponse.json()

    // Check if user is admin
    if (user.email !== ADMIN_EMAIL) {
      return NextResponse.redirect(new URL('/login?error=unauthorized', process.env.NEXTAUTH_URL))
    }

    // Create session JWT
    const secret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET)
    const token = await new SignJWT({
      email: user.email,
      name: user.name,
      picture: user.picture,
      sub: user.id,
    })
      .setProtectedHeader({ alg: 'HS256' })
      .setIssuedAt()
      .setExpirationTime('30d')
      .sign(secret)

    // Set session cookie
    const response = NextResponse.redirect(new URL('/admin', process.env.NEXTAUTH_URL))
    response.cookies.set('session', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 30 * 24 * 60 * 60, // 30 days
      path: '/',
    })

    return response
  } catch (error) {
    console.error('OAuth callback error:', error)
    return NextResponse.redirect(new URL('/login?error=callback_error', process.env.NEXTAUTH_URL))
  }
}
