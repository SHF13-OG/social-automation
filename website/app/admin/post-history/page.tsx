'use client'

import { useEffect, useState, useMemo } from 'react'
import {
  Eye,
  Heart,
  MessageCircle,
  Share2,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  History,
  Clock,
  Film,
  CheckCircle,
  Upload,
} from 'lucide-react'

interface PostHistoryEntry {
  id: number
  post_number: number
  theme_slug: string
  theme_name: string
  theme_hook: string | null
  verse_ref: string
  verse_text: string
  cta: string
  description: string
  hashtags: string
  status: string
  prayer_id: number | null
  prayer_text: string | null
  word_count: number | null
  tiktok_post_id: string | null
  tiktok_views: number | null
  tiktok_likes: number | null
  tiktok_comments: number | null
  tiktok_shares: number | null
  tiktok_favorites: number | null
  tiktok_url: string | null
  video_path: string | null
  created_at: string
  updated_at: string
}

export default function PostHistoryPage() {
  const [entries, setEntries] = useState<PostHistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [themeFilter, setThemeFilter] = useState('all')
  const [expandedPrayers, setExpandedPrayers] = useState<Set<number>>(new Set())

  useEffect(() => {
    fetchEntries()
  }, [statusFilter, themeFilter])

  async function fetchEntries() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (statusFilter !== 'all') params.set('status', statusFilter)
      if (themeFilter !== 'all') params.set('theme', themeFilter)
      const qs = params.toString()
      const url = `/api/post-history${qs ? `?${qs}` : ''}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('Failed to fetch post history')
      const data = await res.json()
      setEntries(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post history')
    } finally {
      setLoading(false)
    }
  }

  const uniqueThemes = useMemo(() => {
    const map = new Map<string, string>()
    entries.forEach((e) => map.set(e.theme_slug, e.theme_name))
    return Array.from(map.entries()).sort((a, b) => a[1].localeCompare(b[1]))
  }, [entries])

  function togglePrayer(id: number) {
    setExpandedPrayers((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  // Summary stats
  const totalPosts = entries.length
  const uploadedCount = entries.filter((e) => e.status === 'uploaded').length
  const withAnalytics = entries.filter((e) => e.tiktok_views !== null).length
  const avgEngagement = useMemo(() => {
    const withViews = entries.filter((e) => e.tiktok_views && e.tiktok_views > 0)
    if (withViews.length === 0) return 0
    const totalRate = withViews.reduce((sum, e) => {
      const engagement = (e.tiktok_likes || 0) + (e.tiktok_comments || 0) + (e.tiktok_shares || 0)
      return sum + (engagement / e.tiktok_views!) * 100
    }, 0)
    return totalRate / withViews.length
  }, [entries])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-cream/70">Loading post history...</div>
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

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-400/20 text-yellow-400',
    generated: 'bg-blue-400/20 text-blue-400',
    approved: 'bg-green-400/20 text-green-400',
    uploaded: 'bg-cream/10 text-cream/50',
  }

  const statusIcons: Record<string, React.ReactNode> = {
    pending: <Clock size={14} />,
    generated: <Film size={14} />,
    approved: <CheckCircle size={14} />,
    uploaded: <Upload size={14} />,
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <History className="w-6 h-6 text-accent-beige" />
          <h1 className="text-2xl font-serif text-accent-beige">Post History</h1>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-navy-charcoal border border-accent-beige/30 text-cream rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-accent-beige"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="generated">Generated</option>
            <option value="approved">Approved</option>
            <option value="uploaded">Uploaded</option>
          </select>
          <select
            value={themeFilter}
            onChange={(e) => setThemeFilter(e.target.value)}
            className="bg-navy-charcoal border border-accent-beige/30 text-cream rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-accent-beige"
          >
            <option value="all">All Themes</option>
            {uniqueThemes.map(([slug, name]) => (
              <option key={slug} value={slug}>
                {name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard icon={<History className="w-5 h-5" />} label="Total Posts" value={totalPosts} color="text-accent-beige" />
        <SummaryCard icon={<Upload className="w-5 h-5" />} label="Uploaded" value={uploadedCount} color="text-cream/50" />
        <SummaryCard icon={<Eye className="w-5 h-5" />} label="With Analytics" value={withAnalytics} color="text-blue-400" />
        <SummaryCard icon={<TrendingUp className="w-5 h-5" />} label="Avg Engagement" value={`${avgEngagement.toFixed(1)}%`} color="text-green-400" />
      </div>

      {/* Post Cards */}
      <div className="space-y-4">
        {entries.length === 0 ? (
          <div className="text-center text-cream/50 py-8">
            No posts found for the selected filters.
          </div>
        ) : (
          entries.map((entry) => (
            <div key={entry.id} className="bg-navy-charcoal/50 rounded-xl p-6">
              {/* Card Header */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-cream/50 text-sm">#{entry.post_number}</span>
                    <span className="text-cream/40 text-xs">
                      {new Date(entry.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="font-serif text-accent-beige">{entry.theme_name}</h3>
                  {entry.theme_hook && (
                    <p className="text-accent-beige/70 text-sm italic mt-1">{entry.theme_hook}</p>
                  )}
                </div>
                <span
                  className={`flex items-center gap-1 text-xs px-2 py-1 rounded whitespace-nowrap ${
                    statusColors[entry.status] || 'bg-gray-400/20 text-gray-400'
                  }`}
                >
                  {statusIcons[entry.status]}
                  {entry.status}
                </span>
              </div>

              {/* Verse */}
              <div className="mb-3">
                <p className="text-cream/90 text-sm font-medium">{entry.verse_ref}</p>
                <p className="text-cream/60 text-sm italic">{entry.verse_text}</p>
              </div>

              {/* Prayer (collapsible) */}
              {entry.prayer_text && (
                <div className="mb-3">
                  <button
                    onClick={() => togglePrayer(entry.id)}
                    className="flex items-center gap-2 text-cream/50 text-xs hover:text-cream/70 transition-colors"
                  >
                    {expandedPrayers.has(entry.id) ? (
                      <ChevronUp size={14} />
                    ) : (
                      <ChevronDown size={14} />
                    )}
                    Prayer{entry.word_count ? ` (${entry.word_count} words)` : ''}
                  </button>
                  {expandedPrayers.has(entry.id) && (
                    <p className="text-cream/60 text-sm mt-2 whitespace-pre-line leading-relaxed">
                      {entry.prayer_text}
                    </p>
                  )}
                </div>
              )}

              {/* Description, Hashtags, CTA */}
              <div className="space-y-1 mb-3">
                <p className="text-cream/50 text-xs">
                  <span className="text-cream/30">Desc:</span> {entry.description}
                </p>
                <p className="text-cream/50 text-xs">
                  <span className="text-cream/30">Tags:</span> {entry.hashtags}
                </p>
                <p className="text-cream/50 text-xs">
                  <span className="text-cream/30">CTA:</span> {entry.cta}
                </p>
                {entry.video_path && (
                  <p className="text-cream/50 text-xs">
                    <span className="text-cream/30">Video:</span>{' '}
                    {entry.video_path.split('/').pop()}
                  </p>
                )}
              </div>

              {/* TikTok Performance Metrics */}
              {entry.tiktok_views !== null && (
                <div className="border-t border-accent-beige/10 pt-3">
                  <div className="grid grid-cols-5 gap-3">
                    <MetricCell icon={<Eye size={14} />} label="Views" value={formatNumber(entry.tiktok_views || 0)} />
                    <MetricCell icon={<Heart size={14} />} label="Likes" value={formatNumber(entry.tiktok_likes || 0)} />
                    <MetricCell icon={<MessageCircle size={14} />} label="Comments" value={formatNumber(entry.tiktok_comments || 0)} />
                    <MetricCell icon={<Share2 size={14} />} label="Shares" value={formatNumber(entry.tiktok_shares || 0)} />
                    <MetricCell
                      icon={<TrendingUp size={14} />}
                      label="Engagement"
                      value={
                        entry.tiktok_views && entry.tiktok_views > 0
                          ? `${(
                              (((entry.tiktok_likes || 0) + (entry.tiktok_comments || 0) + (entry.tiktok_shares || 0)) /
                                entry.tiktok_views) *
                              100
                            ).toFixed(1)}%`
                          : '0%'
                      }
                    />
                  </div>
                  {entry.tiktok_url && (
                    <a
                      href={entry.tiktok_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block mt-2 text-xs text-accent-beige/70 hover:text-accent-beige transition-colors"
                    >
                      View on TikTok →
                    </a>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function SummaryCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode
  label: string
  value: number | string
  color: string
}) {
  return (
    <div className="bg-navy-charcoal/50 rounded-xl p-4">
      <div className={`flex items-center gap-2 ${color} mb-2`}>
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-2xl font-serif text-cream">{value}</div>
    </div>
  )
}

function MetricCell({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="text-center">
      <div className="flex items-center justify-center gap-1 text-cream/40 mb-1">
        {icon}
      </div>
      <div className="text-cream/90 text-sm font-medium">{value}</div>
      <div className="text-cream/40 text-xs">{label}</div>
    </div>
  )
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}
