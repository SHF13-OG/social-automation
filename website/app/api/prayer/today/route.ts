import { NextResponse } from 'next/server'
import { ensureDb, getTodaysPrayer } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    await ensureDb()
    const prayer = getTodaysPrayer()

    if (!prayer) {
      return NextResponse.json(
        { error: 'No prayer found for today' },
        { status: 404 }
      )
    }

    return NextResponse.json({
      prayer_id: prayer.prayer_id,
      verse_ref: prayer.verse_ref,
      verse_text: prayer.verse_text,
      prayer_text: prayer.prayer_text,
      theme: {
        slug: prayer.theme_slug,
        name: prayer.theme_name,
        tone: prayer.tone,
      },
      audio_url: prayer.audio_path ? `/api/audio/${prayer.prayer_id}` : null,
      duration_sec: prayer.duration_sec,
      date: prayer.created_at,
    })
  } catch (error) {
    console.error('Error fetching today\'s prayer:', error)
    return NextResponse.json(
      { error: 'Failed to fetch prayer' },
      { status: 500 }
    )
  }
}
