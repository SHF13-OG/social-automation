// Database connection utilities
// Uses sql.js for SQLite in a Node.js environment

let db: any = null
let initPromise: Promise<any> | null = null

async function initDb(): Promise<any> {
  if (db) return db
  if (initPromise) return initPromise

  initPromise = (async () => {
    try {
      const initSqlJs = (await import('sql.js')).default
      const fs = await import('fs')
      const path = await import('path')

      const SQL = await initSqlJs()
      const DB_PATH = process.env.DB_PATH || path.join(process.cwd(), '..', 'data', 'social.db')

      // Try to load existing database
      if (fs.existsSync(DB_PATH)) {
        const buffer = fs.readFileSync(DB_PATH)
        db = new SQL.Database(buffer)
      } else {
        // Create empty database if file doesn't exist
        db = new SQL.Database()
      }
    } catch (error) {
      console.warn('Could not initialize database:', error)
      db = null
    }

    return db
  })()

  return initPromise
}

export function getDb(): any {
  return db
}

// Initialize on first call
export async function ensureDb(): Promise<any> {
  if (!db) {
    await initDb()
  }
  return db
}

// Helper function to run query and get results
function runQuery<T>(sql: string, params: any[] = []): T[] {
  if (!db) return []

  try {
    const stmt = db.prepare(sql)
    stmt.bind(params)

    const results: T[] = []
    while (stmt.step()) {
      const row = stmt.getAsObject() as T
      results.push(row)
    }
    stmt.free()
    return results
  } catch (error) {
    console.error('Query error:', error)
    return []
  }
}

function runQuerySingle<T>(sql: string, params: any[] = []): T | undefined {
  const results = runQuery<T>(sql, params)
  return results[0]
}

// Helper to get today's prayer
export function getTodaysPrayer(): PrayerData | undefined {
  try {
    return runQuerySingle<PrayerData>(`
      SELECT
        p.id as prayer_id,
        p.prayer_text,
        p.created_at,
        bv.reference as verse_ref,
        bv.text as verse_text,
        t.slug as theme_slug,
        t.name as theme_name,
        t.tone,
        af.file_path as audio_path,
        af.duration_sec
      FROM prayers p
      JOIN bible_verses bv ON p.verse_id = bv.id
      JOIN themes t ON p.theme_id = t.id
      LEFT JOIN audio_files af ON af.prayer_id = p.id
      ORDER BY p.created_at DESC
      LIMIT 1
    `)
  } catch (error) {
    console.error('Error getting today\'s prayer:', error)
    return undefined
  }
}

// Helper to get prayer by date
export function getPrayerByDate(date: string): PrayerData | undefined {
  try {
    return runQuerySingle<PrayerData>(`
      SELECT
        p.id as prayer_id,
        p.prayer_text,
        p.created_at,
        bv.reference as verse_ref,
        bv.text as verse_text,
        t.slug as theme_slug,
        t.name as theme_name,
        t.tone,
        af.file_path as audio_path,
        af.duration_sec
      FROM prayers p
      JOIN bible_verses bv ON p.verse_id = bv.id
      JOIN themes t ON p.theme_id = t.id
      LEFT JOIN audio_files af ON af.prayer_id = p.id
      WHERE date(p.created_at) = ?
      ORDER BY p.created_at DESC
      LIMIT 1
    `, [date])
  } catch (error) {
    console.error('Error getting prayer by date:', error)
    return undefined
  }
}

// Helper to get prayers for archive listing
export function getRecentPrayers(limit: number = 30): PrayerData[] {
  try {
    return runQuery<PrayerData>(`
      SELECT
        p.id as prayer_id,
        p.prayer_text,
        p.created_at,
        bv.reference as verse_ref,
        bv.text as verse_text,
        t.slug as theme_slug,
        t.name as theme_name,
        t.tone,
        af.file_path as audio_path,
        af.duration_sec
      FROM prayers p
      JOIN bible_verses bv ON p.verse_id = bv.id
      JOIN themes t ON p.theme_id = t.id
      LEFT JOIN audio_files af ON af.prayer_id = p.id
      ORDER BY p.created_at DESC
      LIMIT ?
    `, [limit])
  } catch (error) {
    console.error('Error getting recent prayers:', error)
    return []
  }
}

// Helper to get available prayer dates for navigation
export function getAvailableDates(): string[] {
  try {
    const results = runQuery<{ date: string }>(`
      SELECT DISTINCT date(created_at) as date
      FROM prayers
      ORDER BY date DESC
      LIMIT 365
    `)
    return results.map(d => d.date)
  } catch (error) {
    console.error('Error getting available dates:', error)
    return []
  }
}

// Helper to get all themes with stats
export function getThemesWithStats(): ThemeStats[] {
  try {
    return runQuery<ThemeStats>(`
      SELECT
        t.id,
        t.slug,
        t.name,
        t.description,
        t.tone,
        t.is_active,
        COUNT(DISTINCT bv.id) as verse_count,
        COUNT(DISTINCT p.id) as prayer_count,
        COUNT(DISTINCT gv.id) as video_count
      FROM themes t
      LEFT JOIN bible_verses bv ON bv.theme_id = t.id
      LEFT JOIN prayers p ON p.theme_id = t.id
      LEFT JOIN generated_videos gv ON gv.prayer_id = p.id
      GROUP BY t.id
      ORDER BY t.name
    `)
  } catch (error) {
    console.error('Error getting themes:', error)
    return []
  }
}

// Helper to get engagement analytics
export function getAnalytics(days: number = 30) {
  try {
    const posts = runQuery<TikTokPost>(`
      SELECT
        post_id,
        created_at,
        views,
        likes,
        comments,
        shares,
        favorites,
        caption
      FROM tiktok_posts
      WHERE created_at >= datetime('now', '-' || ? || ' days')
      ORDER BY created_at DESC
    `, [days])

    // Calculate metrics
    const totalViews = posts.reduce((sum, p) => sum + (p.views || 0), 0)
    const totalEngagement = posts.reduce((sum, p) =>
      sum + (p.likes || 0) + (p.comments || 0) + (p.shares || 0), 0)
    const avgEngagementRate = totalViews > 0 ? (totalEngagement / totalViews) * 100 : 0

    const viewsArray = posts.map(p => p.views || 0).sort((a, b) => a - b)
    const medianViews = viewsArray.length > 0
      ? viewsArray[Math.floor(viewsArray.length / 2)]
      : 0

    return {
      posts,
      kpis: {
        totalPosts: posts.length,
        totalViews,
        totalEngagement,
        avgEngagementRate: avgEngagementRate.toFixed(2),
        medianViews,
      },
      recommendations: generateRecommendations(avgEngagementRate, medianViews, posts),
    }
  } catch (error) {
    console.error('Error getting analytics:', error)
    return {
      posts: [],
      kpis: {
        totalPosts: 0,
        totalViews: 0,
        totalEngagement: 0,
        avgEngagementRate: '0.00',
        medianViews: 0,
      },
      recommendations: ['Unable to load analytics data.'],
    }
  }
}

function generateRecommendations(engagementRate: number, medianViews: number, posts: TikTokPost[]) {
  const recs: string[] = []

  if (posts.length === 0) {
    recs.push('No posts found in the selected time period.')
    return recs
  }

  if (engagementRate < 2.0) {
    recs.push("Engagement rate is below 2%. Try stronger hooks in the first 1-2 seconds and clearer calls to action.")
  }

  if (medianViews < 500) {
    recs.push("Median views are low. Experiment with different posting times (try 7am vs 7pm) for a week.")
  }

  const totalShares = posts.reduce((sum, p) => sum + (p.shares || 0), 0)
  if (totalShares === 0) {
    recs.push("No shares recorded. Add prompts like 'Send this to someone who needs encouragement today.'")
  }

  if (posts.length < 5) {
    recs.push("Not enough data yet. Continue posting consistently for 2 weeks before making major changes.")
  }

  return recs
}

// Helper to get queue status for schedule page
export function getQueueItems(status?: string): QueueItem[] {
  try {
    let sql = `
      SELECT
        gv.id,
        gv.video_path,
        gv.status,
        gv.created_at,
        gv.publish_at,
        gv.error_message,
        p.prayer_text,
        bv.reference as verse_ref,
        t.name as theme_name
      FROM generated_videos gv
      JOIN prayers p ON gv.prayer_id = p.id
      JOIN bible_verses bv ON p.verse_id = bv.id
      JOIN themes t ON p.theme_id = t.id
    `

    if (status) {
      sql += ` WHERE gv.status = ?`
      sql += ` ORDER BY gv.publish_at ASC, gv.created_at DESC`
      return runQuery<QueueItem>(sql, [status])
    }

    sql += ` ORDER BY gv.publish_at ASC, gv.created_at DESC LIMIT 100`
    return runQuery<QueueItem>(sql)
  } catch (error) {
    console.error('Error getting queue items:', error)
    return []
  }
}

// Helper to update prayer text override
export function updatePrayerText(prayerId: number, prayerText: string) {
  if (!db) throw new Error('Database not available')

  try {
    db.run(`
      UPDATE prayers SET prayer_text = ? WHERE id = ?
    `, [prayerText, prayerId])
  } catch (error) {
    console.error('Error updating prayer text:', error)
    throw error
  }
}

// Helper to update theme
export function updateTheme(id: number, updates: { description?: string; is_active?: boolean }) {
  if (!db) throw new Error('Database not available')

  try {
    const setClauses: string[] = []
    const values: any[] = []

    if (updates.description !== undefined) {
      setClauses.push('description = ?')
      values.push(updates.description)
    }

    if (updates.is_active !== undefined) {
      setClauses.push('is_active = ?')
      values.push(updates.is_active ? 1 : 0)
    }

    if (setClauses.length === 0) return

    values.push(id)
    db.run(`
      UPDATE themes SET ${setClauses.join(', ')} WHERE id = ?
    `, values)
  } catch (error) {
    console.error('Error updating theme:', error)
    throw error
  }
}

// Type definitions
export interface QueueItem {
  id: number
  video_path: string
  status: string
  created_at: string
  publish_at: string | null
  error_message: string | null
  prayer_text: string
  verse_ref: string
  theme_name: string
}

export interface PrayerData {
  prayer_id: number
  prayer_text: string
  created_at: string
  verse_ref: string
  verse_text: string
  theme_slug: string
  theme_name: string
  tone: string
  audio_path: string | null
  duration_sec: number | null
}

export interface ThemeStats {
  id: number
  slug: string
  name: string
  description: string | null
  tone: string
  is_active: number
  verse_count: number
  prayer_count: number
  video_count: number
}

export interface TikTokPost {
  post_id: string
  created_at: string
  views: number
  likes: number
  comments: number
  shares: number
  favorites: number
  caption: string
}

export interface TestRun {
  id: number
  run_id: string
  run_type: 'ci' | 'deploy' | 'daily' | 'manual'
  started_at: string
  completed_at: string | null
  status: 'passed' | 'failed' | 'running'
  tests_total: number
  tests_passed: number
  tests_failed: number
  coverage_percent: number | null
  error_log: string | null
  created_at: string
}

// Helper to get test runs for the dashboard
export function getTestRuns(days: number = 30): TestRun[] {
  try {
    return runQuery<TestRun>(`
      SELECT
        id,
        run_id,
        run_type,
        started_at,
        completed_at,
        status,
        tests_total,
        tests_passed,
        tests_failed,
        coverage_percent,
        error_log,
        created_at
      FROM test_runs
      WHERE created_at >= datetime('now', '-' || ? || ' days')
      ORDER BY created_at DESC
    `, [days])
  } catch (error) {
    console.error('Error getting test runs:', error)
    return []
  }
}

// Helper to save a test run result
export function saveTestRun(run: Omit<TestRun, 'id' | 'created_at'>): void {
  if (!db) throw new Error('Database not available')

  try {
    db.run(`
      INSERT INTO test_runs (
        run_id, run_type, started_at, completed_at, status,
        tests_total, tests_passed, tests_failed, coverage_percent, error_log
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      run.run_id,
      run.run_type,
      run.started_at,
      run.completed_at,
      run.status,
      run.tests_total,
      run.tests_passed,
      run.tests_failed,
      run.coverage_percent,
      run.error_log,
    ])
  } catch (error) {
    console.error('Error saving test run:', error)
    throw error
  }
}
