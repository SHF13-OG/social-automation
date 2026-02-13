import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { ensureDb, getThemesWithStats, updateTheme, saveDb } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  const session = await getSession()

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  await ensureDb()
  const themes = getThemesWithStats()
  return NextResponse.json(themes)
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

    updateTheme(id, updates)
    saveDb()

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error updating theme:', error)
    return NextResponse.json(
      { error: 'Failed to update theme' },
      { status: 500 }
    )
  }
}
