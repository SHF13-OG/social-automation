import { NextRequest, NextResponse } from 'next/server'
import { ensureDb, getDb } from '@/lib/db'
import fs from 'fs'
import path from 'path'

export const dynamic = 'force-dynamic'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const prayerId = parseInt(id, 10)

    if (isNaN(prayerId)) {
      return NextResponse.json({ error: 'Invalid prayer ID' }, { status: 400 })
    }

    // Query using sql.js
    await ensureDb()
    const db = getDb()
    if (!db) {
      return NextResponse.json({ error: 'Database not available' }, { status: 500 })
    }

    const stmt = db.prepare(`
      SELECT file_path as audio_path FROM audio_files WHERE prayer_id = ?
    `)
    stmt.bind([prayerId])

    let audioPath: string | null = null
    if (stmt.step()) {
      const row = stmt.getAsObject() as { audio_path: string | null }
      audioPath = row.audio_path
    }
    stmt.free()

    if (!audioPath) {
      return NextResponse.json({ error: 'Audio not found' }, { status: 404 })
    }

    // Resolve the audio path relative to the data directory
    const dataDir = process.env.DATA_DIR || path.join(process.cwd(), '..', 'data')
    const fullAudioPath = path.join(dataDir, audioPath)

    if (!fs.existsSync(fullAudioPath)) {
      return NextResponse.json({ error: 'Audio file not found' }, { status: 404 })
    }

    const audioBuffer = fs.readFileSync(fullAudioPath)
    const ext = path.extname(fullAudioPath).toLowerCase()

    let contentType = 'audio/mpeg'
    if (ext === '.wav') contentType = 'audio/wav'
    else if (ext === '.ogg') contentType = 'audio/ogg'
    else if (ext === '.m4a') contentType = 'audio/mp4'

    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Length': audioBuffer.length.toString(),
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    })
  } catch (error) {
    console.error('Error serving audio:', error)
    return NextResponse.json({ error: 'Failed to serve audio' }, { status: 500 })
  }
}
