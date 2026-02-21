import { NextResponse } from 'next/server'
import { DB_BASE64 } from '@/lib/db-data'

export const dynamic = 'force-dynamic'

export async function GET() {
  const info: Record<string, unknown> = {
    db_base64_length: DB_BASE64?.length ?? 0,
  }

  try {
    // Step 1: import sql.js asm build (no WASM needed)
    const initSqlJs = (await import('sql.js/dist/sql-asm.js')).default
    info.step1_import = 'ok'

    // Step 2: init sql.js
    const SQL = await initSqlJs()
    info.step2_init = 'ok'

    // Step 3: decode DB
    const clean = DB_BASE64.replace(/\s/g, '')
    const binary = atob(clean)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    info.step3_db_decode = `${bytes.length} bytes`

    // Step 4: create database
    const db = new SQL.Database(bytes)
    info.step4_db_create = 'ok'

    // Step 5: query
    const count = db.exec("SELECT COUNT(*) FROM prayers")
    info.step5_prayer_count = count[0]?.values?.[0]?.[0] ?? 0

    const recent = db.exec(`
      SELECT p.id, substr(p.created_at, 1, 10), bv.reference, t.slug
      FROM prayers p
      JOIN bible_verses bv ON p.verse_id = bv.id
      JOIN themes t ON p.theme_id = t.id
      ORDER BY p.created_at DESC LIMIT 3
    `)
    info.step5_recent = recent[0]?.values ?? []

    db.close()
  } catch (e: any) {
    info.error = e.message
    info.error_stack = e.stack?.split('\n').slice(0, 5)
  }

  return NextResponse.json(info)
}
