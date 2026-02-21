import { NextResponse } from 'next/server'
import { ensureDb, getDb } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  const info: Record<string, unknown> = {}

  try {
    await ensureDb()
    const db = getDb()
    info.db_loaded = !!db

    if (db) {
      const tables = db.exec("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
      info.tables = tables[0]?.values?.map((r: unknown[]) => r[0]) ?? []

      const count = db.exec("SELECT COUNT(*) FROM prayers")
      info.prayer_count = count[0]?.values?.[0]?.[0] ?? 0

      const recent = db.exec(`
        SELECT p.id, substr(p.created_at, 1, 10)
        FROM prayers p ORDER BY p.created_at DESC LIMIT 3
      `)
      info.recent_prayer_dates = recent[0]?.values ?? []
    }
  } catch (e: any) {
    info.error = e.message
    info.stack = e.stack?.split('\n').slice(0, 5)
  }

  return NextResponse.json(info)
}
