import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { ensureDb, getQueueItems } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const session = await getSession()

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  await ensureDb()

  const { searchParams } = new URL(request.url)
  const status = searchParams.get('status') || undefined

  const items = getQueueItems(status)
  return NextResponse.json(items)
}
