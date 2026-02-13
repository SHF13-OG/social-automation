import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const session = await getSession()

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const { searchParams } = new URL(request.url)
    const days = parseInt(searchParams.get('days') || '30', 10)

    // Return empty analytics when database is not available
    // This will be populated when the database is connected
    return NextResponse.json({
      posts: [],
      kpis: {
        totalPosts: 0,
        totalViews: 0,
        totalEngagement: 0,
        avgEngagementRate: '0.00',
        medianViews: 0,
      },
      recommendations: [
        'No data available yet. Analytics will appear once content is published to TikTok.',
      ],
    })
  } catch (error) {
    console.error('Error fetching analytics:', error)
    return NextResponse.json({ error: 'Failed to fetch analytics' }, { status: 500 })
  }
}
