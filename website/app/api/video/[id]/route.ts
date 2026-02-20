import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
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

    const db = getDb()
    if (!db) {
      return NextResponse.json({ error: 'Database not available' }, { status: 500 })
    }

    const stmt = db.prepare(`
      SELECT file_path FROM generated_videos WHERE prayer_id = ? ORDER BY created_at DESC LIMIT 1
    `)
    stmt.bind([prayerId])

    let videoPath: string | null = null
    if (stmt.step()) {
      const row = stmt.getAsObject() as { file_path: string | null }
      videoPath = row.file_path
    }
    stmt.free()

    if (!videoPath) {
      return NextResponse.json({ error: 'Video not found' }, { status: 404 })
    }

    // Resolve the video path — videos are stored relative to the project root
    const projectRoot = process.env.PROJECT_ROOT || path.join(process.cwd(), '..')
    const fullVideoPath = path.join(projectRoot, videoPath)

    if (!fs.existsSync(fullVideoPath)) {
      return NextResponse.json({ error: 'Video file not found' }, { status: 404 })
    }

    const stat = fs.statSync(fullVideoPath)
    const range = request.headers.get('range')

    // Support range requests for video seeking
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-')
      const start = parseInt(parts[0], 10)
      const end = parts[1] ? parseInt(parts[1], 10) : stat.size - 1
      const chunkSize = end - start + 1

      const buffer = Buffer.alloc(chunkSize)
      const fd = fs.openSync(fullVideoPath, 'r')
      fs.readSync(fd, buffer, 0, chunkSize, start)
      fs.closeSync(fd)

      return new NextResponse(buffer, {
        status: 206,
        headers: {
          'Content-Range': `bytes ${start}-${end}/${stat.size}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': chunkSize.toString(),
          'Content-Type': 'video/mp4',
        },
      })
    }

    const videoBuffer = fs.readFileSync(fullVideoPath)
    return new NextResponse(videoBuffer, {
      headers: {
        'Content-Type': 'video/mp4',
        'Content-Length': stat.size.toString(),
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    })
  } catch (error) {
    console.error('Error serving video:', error)
    return NextResponse.json({ error: 'Failed to serve video' }, { status: 500 })
  }
}
