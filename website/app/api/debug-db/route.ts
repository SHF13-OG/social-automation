import { NextResponse } from 'next/server'
import { DB_BASE64 } from '@/lib/db-data'

export const dynamic = 'force-dynamic'

export async function GET() {
  const info: Record<string, unknown> = {
    db_base64_length: DB_BASE64?.length ?? 0,
  }

  // Try approach 1: asm.js build (external package, CJS preserved)
  try {
    const initSqlJs = (await import('sql.js/dist/sql-asm.js')).default
    info.asm_import = 'ok'

    const SQL = await initSqlJs()
    info.asm_init = 'ok'

    const clean = DB_BASE64.replace(/\s/g, '')
    const binary = atob(clean)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }

    const db = new SQL.Database(bytes)
    info.asm_db = 'ok'

    const count = db.exec("SELECT COUNT(*) FROM prayers")
    info.asm_prayer_count = count[0]?.values?.[0]?.[0] ?? 0

    db.close()
    info.approach = 'asm'
    return NextResponse.json(info)
  } catch (e: any) {
    info.asm_error = e.message
  }

  // Try approach 2: default sql.js (wasm) - expected to fail on CF Workers
  try {
    const initSqlJs = (await import('sql.js')).default
    info.wasm_import = 'ok'

    const SQL = await initSqlJs()
    info.wasm_init = 'ok'
    info.approach = 'wasm'
    return NextResponse.json(info)
  } catch (e: any) {
    info.wasm_error = e.message
  }

  return NextResponse.json(info)
}
