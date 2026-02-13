'use client'

import { useEffect, useState } from 'react'
import { Calendar, Clock, CheckCircle, XCircle, Loader, AlertCircle } from 'lucide-react'

interface QueueItem {
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

export default function SchedulePage() {
  const [items, setItems] = useState<QueueItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    fetchQueue()
  }, [filter])

  async function fetchQueue() {
    setLoading(true)
    try {
      const url = filter === 'all' ? '/api/queue' : `/api/queue?status=${filter}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('Failed to fetch queue')
      const data = await res.json()
      setItems(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load queue')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-cream/70">Loading schedule...</div>
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

  const statusCounts = items.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-serif text-accent-beige">Schedule & Queue</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-navy-charcoal border border-accent-beige/30 text-cream rounded-lg px-4 py-2 focus:outline-none focus:border-accent-beige"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatusCard
          icon={<Clock className="w-5 h-5" />}
          label="Pending"
          count={statusCounts['pending'] || 0}
          color="text-yellow-400"
        />
        <StatusCard
          icon={<Loader className="w-5 h-5" />}
          label="Processing"
          count={statusCounts['processing'] || 0}
          color="text-blue-400"
        />
        <StatusCard
          icon={<CheckCircle className="w-5 h-5" />}
          label="Completed"
          count={statusCounts['completed'] || 0}
          color="text-green-400"
        />
        <StatusCard
          icon={<XCircle className="w-5 h-5" />}
          label="Failed"
          count={statusCounts['failed'] || 0}
          color="text-red-400"
        />
      </div>

      {/* Queue Items */}
      <div className="space-y-4">
        {items.length === 0 ? (
          <div className="text-center text-cream/50 py-8">
            No items in queue
          </div>
        ) : (
          items.map((item) => (
            <QueueItemCard key={item.id} item={item} />
          ))
        )}
      </div>
    </div>
  )
}

function StatusCard({
  icon,
  label,
  count,
  color,
}: {
  icon: React.ReactNode
  label: string
  count: number
  color: string
}) {
  return (
    <div className="bg-navy-charcoal/50 rounded-xl p-4">
      <div className={`flex items-center gap-2 ${color} mb-2`}>
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-2xl font-serif text-cream">{count}</div>
    </div>
  )
}

function QueueItemCard({ item }: { item: QueueItem }) {
  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-400/20 text-yellow-400',
    processing: 'bg-blue-400/20 text-blue-400',
    completed: 'bg-green-400/20 text-green-400',
    failed: 'bg-red-400/20 text-red-400',
  }

  const statusIcons: Record<string, React.ReactNode> = {
    pending: <Clock size={14} />,
    processing: <Loader size={14} className="animate-spin" />,
    completed: <CheckCircle size={14} />,
    failed: <XCircle size={14} />,
  }

  return (
    <div className="bg-navy-charcoal/50 rounded-xl p-6">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h3 className="font-serif text-accent-beige">{item.verse_ref}</h3>
            <span className="text-xs px-2 py-1 bg-accent-beige/20 text-accent-beige/80 rounded">
              {item.theme_name}
            </span>
          </div>
          {item.publish_at && (
            <p className="text-cream/50 text-sm flex items-center gap-1">
              <Calendar size={14} />
              Scheduled: {new Date(item.publish_at).toLocaleString()}
            </p>
          )}
        </div>
        <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded ${statusColors[item.status] || 'bg-gray-400/20 text-gray-400'}`}>
          {statusIcons[item.status]}
          {item.status}
        </span>
      </div>

      <p className="text-cream/70 text-sm line-clamp-2 mb-2">
        {item.prayer_text}
      </p>

      {item.error_message && (
        <div className="flex items-start gap-2 mt-3 p-3 bg-red-900/20 rounded-lg">
          <AlertCircle size={16} className="text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-400 text-sm">{item.error_message}</p>
        </div>
      )}
    </div>
  )
}
