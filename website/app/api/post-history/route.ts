import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { ensureDb, getPostHistory } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  await ensureDb()

  const { searchParams } = new URL(request.url)
  const status = searchParams.get('status') || undefined
  const themeSlug = searchParams.get('theme') || undefined
  const limitParam = searchParams.get('limit')
  const limit = limitParam ? parseInt(limitParam, 10) : undefined

  const entries = getPostHistory({ status, themeSlug, limit })
  return NextResponse.json(entries)
}
