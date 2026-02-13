'use client'

import { useEffect, useState } from 'react'
import {
  Clock,
  Film,
  CheckCircle,
  Upload,
  Edit2,
  Save,
  X,
  Copy,
  Check,
} from 'lucide-react'

interface LineupEntry {
  id: number
  post_number: number
  theme_slug: string
  theme_name: string
  verse_ref: string
  verse_text: string
  cta: string
  description: string
  hashtags: string
  status: string
  prayer_id: number | null
  video_id: number | null
  video_path: string | null
  created_at: string
  updated_at: string
}

export default function LineupPage() {
  const [entries, setEntries] = useState<LineupEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    fetchEntries()
  }, [filter])

  async function fetchEntries() {
    setLoading(true)
    try {
      const url = filter === 'all' ? '/api/lineup' : `/api/lineup?status=${filter}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('Failed to fetch lineup')
      const data = await res.json()
      setEntries(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lineup')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-cream/70">Loading lineup...</div>
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

  const statusCounts = entries.reduce((acc, e) => {
    acc[e.status] = (acc[e.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-serif text-accent-beige">Lineup</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-navy-charcoal border border-accent-beige/30 text-cream rounded-lg px-4 py-2 focus:outline-none focus:border-accent-beige"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="generated">Generated</option>
          <option value="approved">Approved</option>
          <option value="uploaded">Uploaded</option>
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
          icon={<Film className="w-5 h-5" />}
          label="Generated"
          count={statusCounts['generated'] || 0}
          color="text-blue-400"
        />
        <StatusCard
          icon={<CheckCircle className="w-5 h-5" />}
          label="Approved"
          count={statusCounts['approved'] || 0}
          color="text-green-400"
        />
        <StatusCard
          icon={<Upload className="w-5 h-5" />}
          label="Uploaded"
          count={statusCounts['uploaded'] || 0}
          color="text-cream/50"
        />
      </div>

      {/* Lineup Entries */}
      <div className="space-y-4">
        {entries.length === 0 ? (
          <div className="text-center text-cream/50 py-8">
            No lineup entries. Run: <code className="text-accent-beige/70">python -m src.main preview-lineup --count 7</code>
          </div>
        ) : (
          entries.map((entry) => (
            <LineupEntryCard key={entry.id} entry={entry} onUpdate={fetchEntries} />
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

function LineupEntryCard({
  entry,
  onUpdate,
}: {
  entry: LineupEntry
  onUpdate: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [copied, setCopied] = useState(false)
  const [editCta, setEditCta] = useState(entry.cta)
  const [editDescription, setEditDescription] = useState(entry.description)
  const [editHashtags, setEditHashtags] = useState(entry.hashtags)

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

  async function updateEntry(updates: Record<string, string>) {
    setSaving(true)
    try {
      const res = await fetch('/api/lineup', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: entry.id, ...updates }),
      })
      if (!res.ok) throw new Error('Failed to update')
      onUpdate()
      setEditing(false)
    } catch {
      // silently fail — user sees no change
    } finally {
      setSaving(false)
    }
  }

  function handleSave() {
    updateEntry({
      cta: editCta,
      description: editDescription,
      hashtags: editHashtags,
    })
  }

  function handleApprove() {
    updateEntry({ status: 'approved' })
  }

  function handleMarkUploaded() {
    updateEntry({ status: 'uploaded' })
  }

  function handleCopyCaption() {
    const caption = entry.description + '\n\n' + entry.hashtags
    navigator.clipboard.writeText(caption).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function startEditing() {
    setEditCta(entry.cta)
    setEditDescription(entry.description)
    setEditHashtags(entry.hashtags)
    setEditing(true)
  }

  return (
    <div className="bg-navy-charcoal/50 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-cream/50 text-sm">#{entry.post_number}</span>
            <h3 className="font-serif text-accent-beige">{entry.verse_ref}</h3>
            <span className="text-xs px-2 py-1 bg-accent-beige/20 text-accent-beige/80 rounded">
              {entry.theme_name}
            </span>
          </div>
        </div>
        <span
          className={`flex items-center gap-1 text-xs px-2 py-1 rounded ${
            statusColors[entry.status] || 'bg-gray-400/20 text-gray-400'
          }`}
        >
          {statusIcons[entry.status]}
          {entry.status}
        </span>
      </div>

      {/* Body */}
      {editing ? (
        <div className="space-y-3 mb-4">
          <div>
            <label className="block text-xs text-cream/50 mb-1">CTA</label>
            <input
              value={editCta}
              onChange={(e) => setEditCta(e.target.value)}
              className="w-full bg-navy border border-accent-beige/30 text-cream rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent-beige"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/50 mb-1">Description</label>
            <input
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              className="w-full bg-navy border border-accent-beige/30 text-cream rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent-beige"
            />
          </div>
          <div>
            <label className="block text-xs text-cream/50 mb-1">Hashtags</label>
            <input
              value={editHashtags}
              onChange={(e) => setEditHashtags(e.target.value)}
              className="w-full bg-navy border border-accent-beige/30 text-cream rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent-beige"
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-accent-beige text-navy rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 text-sm"
            >
              <Save size={14} />
              Save
            </button>
            <button
              onClick={() => setEditing(false)}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 border border-accent-beige/30 text-cream rounded-lg hover:bg-navy/50 transition-colors disabled:opacity-50 text-sm"
            >
              <X size={14} />
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-1 mb-4">
          <p className="text-cream/70 text-sm line-clamp-2">{entry.verse_text}</p>
          <p className="text-cream/50 text-xs">
            <span className="text-cream/30">CTA:</span> {entry.cta}
          </p>
          <p className="text-cream/50 text-xs">
            <span className="text-cream/30">Desc:</span> {entry.description}
          </p>
          <p className="text-cream/50 text-xs">
            <span className="text-cream/30">Tags:</span> {entry.hashtags}
          </p>
          {entry.video_path && (
            <p className="text-cream/50 text-xs">
              <span className="text-cream/30">Video:</span>{' '}
              {entry.video_path.split('/').pop()}
            </p>
          )}
        </div>
      )}

      {/* Actions */}
      {!editing && (
        <div className="flex items-center gap-2 flex-wrap">
          {entry.status !== 'uploaded' && (
            <button
              onClick={startEditing}
              className="flex items-center gap-1 px-3 py-1.5 text-xs border border-accent-beige/30 text-cream/70 rounded-lg hover:bg-navy/50 transition-colors"
            >
              <Edit2 size={12} />
              Edit
            </button>
          )}

          {entry.status === 'generated' && (
            <button
              onClick={handleApprove}
              disabled={saving}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              <CheckCircle size={12} />
              Approve
            </button>
          )}

          {entry.status === 'approved' && (
            <button
              onClick={handleMarkUploaded}
              disabled={saving}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-accent-beige text-navy rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              <Upload size={12} />
              Mark Uploaded
            </button>
          )}

          {(entry.status === 'generated' || entry.status === 'approved') && (
            <button
              onClick={handleCopyCaption}
              className="flex items-center gap-1 px-3 py-1.5 text-xs border border-accent-beige/30 text-cream/70 rounded-lg hover:bg-navy/50 transition-colors"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? 'Copied!' : 'Copy Caption'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
