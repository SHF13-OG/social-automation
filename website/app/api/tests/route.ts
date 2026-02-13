import { NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { ensureDb, getTestRuns } from '@/lib/db'

export async function GET() {
  const session = await getSession()

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    await ensureDb()
    const testRuns = getTestRuns(30)

    // Calculate summary stats
    const totalRuns = testRuns.length
    const passedRuns = testRuns.filter((r) => r.status === 'passed').length
    const failedRuns = testRuns.filter((r) => r.status === 'failed').length
    const passRate = totalRuns > 0 ? ((passedRuns / totalRuns) * 100).toFixed(1) : '0.0'

    // Group by run type for breakdown
    const byType = {
      ci: testRuns.filter((r) => r.run_type === 'ci'),
      deploy: testRuns.filter((r) => r.run_type === 'deploy'),
      daily: testRuns.filter((r) => r.run_type === 'daily'),
      manual: testRuns.filter((r) => r.run_type === 'manual'),
    }

    // Calculate average coverage
    const runsWithCoverage = testRuns.filter((r) => r.coverage_percent !== null)
    const avgCoverage =
      runsWithCoverage.length > 0
        ? (
            runsWithCoverage.reduce((sum, r) => sum + (r.coverage_percent || 0), 0) /
            runsWithCoverage.length
          ).toFixed(1)
        : null

    return NextResponse.json({
      runs: testRuns,
      summary: {
        totalRuns,
        passedRuns,
        failedRuns,
        passRate,
        avgCoverage,
      },
      byType: {
        ci: byType.ci.length,
        deploy: byType.deploy.length,
        daily: byType.daily.length,
        manual: byType.manual.length,
      },
    })
  } catch (error) {
    console.error('Error fetching test runs:', error)
    // Return empty data when database not available
    return NextResponse.json({
      runs: [],
      summary: {
        totalRuns: 0,
        passedRuns: 0,
        failedRuns: 0,
        passRate: '0.0',
        avgCoverage: null,
      },
      byType: {
        ci: 0,
        deploy: 0,
        daily: 0,
        manual: 0,
      },
    })
  }
}
