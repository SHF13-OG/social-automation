import { NextResponse } from 'next/server'
import { ensureDb, getDb } from '@/lib/db'
import { DB_BASE64 } from '@/lib/db-data'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const dbInstance = await ensureDb()
    const db = getDb()

    const info: Record<string, unknown> = {
      db_base64_length: DB_BASE64?.length ?? 0,
      db_loaded: !!db,
    }

    if (db) {
      // Check what tables exist
      try {
        const tables = db.exec("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        info.tables = tables[0]?.values?.map((r: string[]) => r[0]) ?? []
      } catch (e: any) {
        info.tables_error = e.message
      }

      // Count prayers
      try {
        const result = db.exec("SELECT COUNT(*) FROM prayers")
        info.prayer_count = result[0]?.values?.[0]?.[0] ?? 0
      } catch (e: any) {
        info.prayer_count_error = e.message
      }

      // Try the actual query
      try {
        const result = db.exec(`
          SELECT p.id, p.created_at, bv.reference, t.slug
          FROM prayers p
          JOIN bible_verses bv ON p.verse_id = bv.id
          JOIN themes t ON p.theme_id = t.id
          ORDER BY p.created_at DESC
          LIMIT 3
        `)
        info.recent_prayers = result[0]?.values ?? []
      } catch (e: any) {
        info.recent_prayers_error = e.message
      }
    }

    return NextResponse.json(info)
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
