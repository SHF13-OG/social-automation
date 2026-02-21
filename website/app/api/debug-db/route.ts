import { NextResponse } from 'next/server'
import { DB_BASE64 } from '@/lib/db-data'

export const dynamic = 'force-dynamic'

export async function GET() {
  const info: Record<string, unknown> = {
    db_base64_length: DB_BASE64?.length ?? 0,
    db_base64_first50: DB_BASE64?.substring(0, 50) ?? '',
  }

  // Step 1: Try importing sql.js
  try {
    const initSqlJs = (await import('sql.js')).default
    info.sqljs_imported = true

    const SQL = await initSqlJs()
    info.sqljs_initialized = true

    // Step 2: Try decoding base64
    try {
      const clean = DB_BASE64.replace(/\s/g, '')
      info.clean_length = clean.length
      const binary = atob(clean)
      info.binary_length = binary.length
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i)
      }
      info.bytes_length = bytes.length
      info.first_bytes = Array.from(bytes.slice(0, 16)).map(b => b.toString(16).padStart(2, '0')).join(' ')

      // Step 3: Try creating DB
      try {
        const db = new SQL.Database(bytes)
        info.db_created = true

        const tables = db.exec("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        info.tables = tables[0]?.values?.map((r: string[]) => r[0]) ?? []

        const count = db.exec("SELECT COUNT(*) FROM prayers")
        info.prayer_count = count[0]?.values?.[0]?.[0] ?? 0

        const recent = db.exec(`
          SELECT p.id, substr(p.created_at, 1, 10)
          FROM prayers p ORDER BY p.created_at DESC LIMIT 3
        `)
        info.recent_prayer_dates = recent[0]?.values ?? []

        db.close()
      } catch (e: any) {
        info.db_create_error = e.message
      }
    } catch (e: any) {
      info.base64_decode_error = e.message
    }
  } catch (e: any) {
    info.sqljs_error = e.message
  }

  return NextResponse.json(info)
}
