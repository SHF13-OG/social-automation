import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { ensureDb, getLineupEntries, updateLineupEntry, saveDb } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  await ensureDb()

  const { searchParams } = new URL(request.url)
  const status = searchParams.get('status') || undefined

  const entries = getLineupEntries(status)
  return NextResponse.json(entries)
}

export async function PUT(request: NextRequest) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  await ensureDb()

  try {
    const body = await request.json()
    const { id, ...updates } = body

    if (!id) {
      return NextResponse.json({ error: 'Missing id' }, { status: 400 })
    }

    updateLineupEntry(id, updates)
    saveDb()

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error updating lineup entry:', error)
    return NextResponse.json(
      { error: 'Failed to update lineup entry' },
      { status: 500 }
    )
  }
}
