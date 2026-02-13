'use client'

import { useEffect, useState } from 'react'
import { BookOpen, Edit2, Save, X, Volume2 } from 'lucide-react'

interface Prayer {
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

export default function PrayersPage() {
  const [prayers, setPrayers] = useState<Prayer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchPrayers()
  }, [])

  async function fetchPrayers() {
    try {
      const res = await fetch('/api/prayers?limit=50')
      if (!res.ok) throw new Error('Failed to fetch prayers')
      const data = await res.json()
      setPrayers(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load prayers')
    } finally {
      setLoading(false)
    }
  }

  async function savePrayer(prayer: Prayer) {
    setSaving(true)
    try {
      const res = await fetch('/api/prayers', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prayer_id: prayer.prayer_id, prayer_text: editText }),
      })
      if (!res.ok) throw new Error('Failed to update prayer')
      await fetchPrayers()
      setEditingId(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update prayer')
    } finally {
      setSaving(false)
    }
  }

  function startEditing(prayer: Prayer) {
    setEditingId(prayer.prayer_id)
    setEditText(prayer.prayer_text)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-cream/70">Loading prayers...</div>
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

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-serif text-accent-beige">Prayers</h1>
        <div className="text-sm text-cream/50">
          {prayers.length} prayers
        </div>
      </div>

      <div className="space-y-4">
        {prayers.map((prayer) => {
          const isEditing = editingId === prayer.prayer_id
          const date = new Date(prayer.created_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })

          return (
            <div key={prayer.prayer_id} className="bg-navy-charcoal/50 rounded-xl p-6">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-serif text-accent-beige">{prayer.verse_ref}</h3>
                    <span className="text-xs px-2 py-1 bg-accent-beige/20 text-accent-beige/80 rounded">
                      {prayer.theme_name}
                    </span>
                    {prayer.audio_path && (
                      <span className="text-green-400">
                        <Volume2 size={14} />
                      </span>
                    )}
                  </div>
                  <p className="text-cream/50 text-sm">{date}</p>
                </div>
                {!isEditing && (
                  <button
                    onClick={() => startEditing(prayer)}
                    className="p-2 text-cream/50 hover:text-cream hover:bg-navy/50 rounded-lg transition-colors"
                    title="Edit Prayer"
                  >
                    <Edit2 size={18} />
                  </button>
                )}
              </div>

              <p className="text-cream/70 text-sm italic mb-4">
                &ldquo;{prayer.verse_text}&rdquo;
              </p>

              {isEditing ? (
                <div className="space-y-3">
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    className="w-full bg-navy border border-accent-beige/30 text-cream rounded-lg px-4 py-3 focus:outline-none focus:border-accent-beige resize-none"
                    rows={6}
                  />
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => savePrayer(prayer)}
                      disabled={saving}
                      className="flex items-center gap-2 px-4 py-2 bg-accent-beige text-navy rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                    >
                      <Save size={16} />
                      Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      disabled={saving}
                      className="flex items-center gap-2 px-4 py-2 border border-accent-beige/30 text-cream rounded-lg hover:bg-navy/50 transition-colors disabled:opacity-50"
                    >
                      <X size={16} />
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-cream/80 text-sm leading-relaxed">
                  {prayer.prayer_text}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
