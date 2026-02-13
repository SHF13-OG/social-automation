import { cookies } from 'next/headers'
import { jwtVerify } from 'jose'

export interface Session {
  user: {
    email: string
    name: string
    image: string
  }
}

export async function getSession(): Promise<Session | null> {
  try {
    const cookieStore = await cookies()
    const sessionCookie = cookieStore.get('session')

    if (!sessionCookie?.value) {
      return null
    }

    const secret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET)
    const { payload } = await jwtVerify(sessionCookie.value, secret)

    return {
      user: {
        email: payload.email as string,
        name: payload.name as string,
        image: payload.picture as string,
      }
    }
  } catch (error) {
    return null
  }
}
