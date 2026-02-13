'use client'

import { useEffect, useState } from 'react'
import { Eye, Heart, MessageCircle, Share2, TrendingUp, AlertCircle } from 'lucide-react'
import EngagementChart from '@/components/EngagementChart'

interface Analytics {
  posts: Array<{
    post_id: string
    created_at: string
    views: number
    likes: number
    comments: number
    shares: number
    favorites: number
    caption: string
  }>
  kpis: {
    totalPosts: number
    totalViews: number
    totalEngagement: number
    avgEngagementRate: string
    medianViews: number
  }
  recommendations: string[]
}

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)

  useEffect(() => {
    async function fetchAnalytics() {
      setLoading(true)
      try {
        const res = await fetch(`/api/analytics?days=${days}`)
        if (!res.ok) throw new Error('Failed to fetch analytics')
        const data = await res.json()
        setAnalytics(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics')
      } finally {
        setLoading(false)
      }
    }
    fetchAnalytics()
  }, [days])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-cream/70">Loading analytics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
        <p className="text-red-400">{error}</p>
      </div>
    )
  }

  if (!analytics) return null

  const { kpis, posts, recommendations } = analytics

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-serif text-accent-beige">Dashboard</h1>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-navy-charcoal border border-accent-beige/30 text-cream rounded-lg px-4 py-2 focus:outline-none focus:border-accent-beige"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          icon={<Eye className="w-5 h-5" />}
          label="Total Views"
          value={formatNumber(kpis.totalViews)}
        />
        <KPICard
          icon={<Heart className="w-5 h-5" />}
          label="Total Engagement"
          value={formatNumber(kpis.totalEngagement)}
        />
        <KPICard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Avg Engagement Rate"
          value={`${kpis.avgEngagementRate}%`}
        />
        <KPICard
          icon={<MessageCircle className="w-5 h-5" />}
          label="Median Views"
          value={formatNumber(kpis.medianViews)}
        />
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-navy-charcoal/50 rounded-2xl p-6">
          <h2 className="text-lg font-serif text-accent-beige mb-4">Views Over Time</h2>
          <EngagementChart posts={posts} type="views" />
        </div>
        <div className="bg-navy-charcoal/50 rounded-2xl p-6">
          <h2 className="text-lg font-serif text-accent-beige mb-4">Engagement Rate</h2>
          <EngagementChart posts={posts} type="engagement" />
        </div>
      </div>

      {/* AI Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-navy-charcoal/50 rounded-2xl p-6">
          <h2 className="text-lg font-serif text-accent-beige mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Recommendations
          </h2>
          <ul className="space-y-3">
            {recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-3 text-cream/80">
                <span className="w-6 h-6 rounded-full bg-accent-beige/20 text-accent-beige flex items-center justify-center text-sm flex-shrink-0">
                  {index + 1}
                </span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recent Posts */}
      <div className="bg-navy-charcoal/50 rounded-2xl p-6">
        <h2 className="text-lg font-serif text-accent-beige mb-4">Recent Posts</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-accent-beige/20">
                <th className="text-left py-3 text-cream/70 font-normal">Date</th>
                <th className="text-right py-3 text-cream/70 font-normal">Views</th>
                <th className="text-right py-3 text-cream/70 font-normal">Likes</th>
                <th className="text-right py-3 text-cream/70 font-normal">Comments</th>
                <th className="text-right py-3 text-cream/70 font-normal">Shares</th>
                <th className="text-right py-3 text-cream/70 font-normal">Rate</th>
              </tr>
            </thead>
            <tbody>
              {posts.slice(0, 10).map((post) => {
                const engagement = (post.likes || 0) + (post.comments || 0) + (post.shares || 0)
                const rate = post.views > 0 ? ((engagement / post.views) * 100).toFixed(2) : '0.00'
                return (
                  <tr key={post.post_id} className="border-b border-accent-beige/10">
                    <td className="py-3 text-cream">
                      {new Date(post.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="py-3 text-right text-cream">{formatNumber(post.views)}</td>
                    <td className="py-3 text-right text-cream">{formatNumber(post.likes)}</td>
                    <td className="py-3 text-right text-cream">{formatNumber(post.comments)}</td>
                    <td className="py-3 text-right text-cream">{formatNumber(post.shares)}</td>
                    <td className="py-3 text-right text-accent-beige">{rate}%</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function KPICard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="bg-navy-charcoal/50 rounded-xl p-4">
      <div className="flex items-center gap-2 text-accent-beige/70 mb-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-2xl font-serif text-accent-beige">{value}</div>
    </div>
  )
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}
