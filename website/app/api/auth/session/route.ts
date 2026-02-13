import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { jwtVerify } from 'jose'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const cookieStore = await cookies()
    const sessionCookie = cookieStore.get('session')

    if (!sessionCookie?.value) {
      return NextResponse.json({ user: null })
    }

    const secret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET)
    const { payload } = await jwtVerify(sessionCookie.value, secret)

    return NextResponse.json({
      user: {
        email: payload.email,
        name: payload.name,
        image: payload.picture,
      }
    })
  } catch (error) {
    return NextResponse.json({ user: null })
  }
}
