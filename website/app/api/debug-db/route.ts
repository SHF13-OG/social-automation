import { NextResponse } from 'next/server'
import { DB_BASE64, WASM_BASE64 } from '@/lib/db-data'

export const dynamic = 'force-dynamic'

export async function GET() {
  const info: Record<string, unknown> = {
    db_base64_length: DB_BASE64?.length ?? 0,
    wasm_base64_length: WASM_BASE64?.length ?? 0,
  }

  try {
    // Step 1: import sql.js
    const initSqlJs = (await import('sql.js')).default
    info.step1_import = 'ok'

    // Step 2: decode WASM
    const wasmClean = WASM_BASE64.replace(/\s/g, '')
    const wasmBinary = atob(wasmClean)
    const wasmBytes = new Uint8Array(wasmBinary.length)
    for (let i = 0; i < wasmBinary.length; i++) {
      wasmBytes[i] = wasmBinary.charCodeAt(i)
    }
    info.step2_wasm_decode = `${wasmBytes.length} bytes`

    // Step 3: init sql.js with WASM binary
    const SQL = await initSqlJs({ wasmBinary: wasmBytes.buffer as ArrayBuffer })
    info.step3_sqljs_init = 'ok'

    // Step 4: decode DB
    const dbClean = DB_BASE64.replace(/\s/g, '')
    const dbBinary = atob(dbClean)
    const dbBytes = new Uint8Array(dbBinary.length)
    for (let i = 0; i < dbBinary.length; i++) {
      dbBytes[i] = dbBinary.charCodeAt(i)
    }
    info.step4_db_decode = `${dbBytes.length} bytes`
    info.step4_db_header = String.fromCharCode(...Array.from(dbBytes.slice(0, 16)))

    // Step 5: create database
    const db = new SQL.Database(dbBytes)
    info.step5_db_create = 'ok'

    // Step 6: query
    const count = db.exec("SELECT COUNT(*) FROM prayers")
    info.step6_prayer_count = count[0]?.values?.[0]?.[0] ?? 0

    db.close()
  } catch (e: any) {
    info.error = e.message
    info.error_stack = e.stack?.split('\n').slice(0, 5)
  }

  return NextResponse.json(info)
}
