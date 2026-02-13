'use client'

import { useEffect, useState } from 'react'
import { Palette, BookOpen, Video, Check, X, Edit2, Save } from 'lucide-react'

interface Theme {
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

export default function ThemesPage() {
  const [themes, setThemes] = useState<Theme[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editDescription, setEditDescription] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchThemes()
  }, [])

  async function fetchThemes() {
    try {
      const res = await fetch('/api/themes')
      if (!res.ok) throw new Error('Failed to fetch themes')
      const data = await res.json()
      setThemes(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load themes')
    } finally {
      setLoading(false)
    }
  }

  async function toggleActive(theme: Theme) {
    setSaving(true)
    try {
      const res = await fetch('/api/themes', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: theme.id, is_active: !theme.is_active }),
      })
      if (!res.ok) throw new Error('Failed to update theme')
      await fetchThemes()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update theme')
    } finally {
      setSaving(false)
    }
  }

  async function saveDescription(theme: Theme) {
    setSaving(true)
    try {
      const res = await fetch('/api/themes', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: theme.id, description: editDescription }),
      })
      if (!res.ok) throw new Error('Failed to update theme')
      await fetchThemes()
      setEditingId(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update theme')
    } finally {
      setSaving(false)
    }
  }

  function startEditing(theme: Theme) {
    setEditingId(theme.id)
    setEditDescription(theme.description || '')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-cream/70">Loading themes...</div>
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

  const activeThemes = themes.filter((t) => t.is_active)
  const inactiveThemes = themes.filter((t) => !t.is_active)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-serif text-accent-beige">Themes & CTAs</h1>
        <div className="text-sm text-cream/50">
          {activeThemes.length} active / {themes.length} total
        </div>
      </div>

      {/* Active Themes */}
      <div>
        <h2 className="text-lg text-accent-beige/70 mb-4">Active Themes</h2>
        <div className="grid gap-4">
          {activeThemes.map((theme) => (
            <ThemeCard
              key={theme.id}
              theme={theme}
              isEditing={editingId === theme.id}
              editDescription={editDescription}
              setEditDescription={setEditDescription}
              onStartEdit={() => startEditing(theme)}
              onSave={() => saveDescription(theme)}
              onCancel={() => setEditingId(null)}
              onToggleActive={() => toggleActive(theme)}
              saving={saving}
            />
          ))}
        </div>
      </div>

      {/* Inactive Themes */}
      {inactiveThemes.length > 0 && (
        <div>
          <h2 className="text-lg text-accent-beige/70 mb-4">Inactive Themes</h2>
          <div className="grid gap-4">
            {inactiveThemes.map((theme) => (
              <ThemeCard
                key={theme.id}
                theme={theme}
                isEditing={editingId === theme.id}
                editDescription={editDescription}
                setEditDescription={setEditDescription}
                onStartEdit={() => startEditing(theme)}
                onSave={() => saveDescription(theme)}
                onCancel={() => setEditingId(null)}
                onToggleActive={() => toggleActive(theme)}
                saving={saving}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ThemeCard({
  theme,
  isEditing,
  editDescription,
  setEditDescription,
  onStartEdit,
  onSave,
  onCancel,
  onToggleActive,
  saving,
}: {
  theme: Theme
  isEditing: boolean
  editDescription: string
  setEditDescription: (value: string) => void
  onStartEdit: () => void
  onSave: () => void
  onCancel: () => void
  onToggleActive: () => void
  saving: boolean
}) {
  return (
    <div
      className={`bg-navy-charcoal/50 rounded-xl p-6 ${
        !theme.is_active ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-serif text-accent-beige">{theme.name}</h3>
            <span className="text-xs px-2 py-1 bg-accent-beige/20 text-accent-beige/80 rounded">
              {theme.tone}
            </span>
          </div>

          {isEditing ? (
            <div className="space-y-3">
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="Enter CTA / description for this theme..."
                className="w-full bg-navy border border-accent-beige/30 text-cream rounded-lg px-4 py-3 focus:outline-none focus:border-accent-beige resize-none"
                rows={3}
              />
              <div className="flex items-center gap-2">
                <button
                  onClick={onSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-accent-beige text-navy rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  <Save size={16} />
                  Save
                </button>
                <button
                  onClick={onCancel}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 border border-accent-beige/30 text-cream rounded-lg hover:bg-navy/50 transition-colors disabled:opacity-50"
                >
                  <X size={16} />
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="text-cream/70 text-sm mb-3">
                {theme.description || 'No CTA set'}
              </p>
              <div className="flex items-center gap-4 text-sm text-cream/50">
                <span className="flex items-center gap-1">
                  <BookOpen size={14} />
                  {theme.verse_count} verses
                </span>
                <span className="flex items-center gap-1">
                  <Palette size={14} />
                  {theme.prayer_count} prayers
                </span>
                <span className="flex items-center gap-1">
                  <Video size={14} />
                  {theme.video_count} videos
                </span>
              </div>
            </>
          )}
        </div>

        {!isEditing && (
          <div className="flex items-center gap-2">
            <button
              onClick={onStartEdit}
              className="p-2 text-cream/50 hover:text-cream hover:bg-navy/50 rounded-lg transition-colors"
              title="Edit CTA"
            >
              <Edit2 size={18} />
            </button>
            <button
              onClick={onToggleActive}
              disabled={saving}
              className={`p-2 rounded-lg transition-colors ${
                theme.is_active
                  ? 'text-green-400 hover:bg-green-400/10'
                  : 'text-cream/50 hover:bg-navy/50'
              }`}
              title={theme.is_active ? 'Deactivate' : 'Activate'}
            >
              {theme.is_active ? <Check size={18} /> : <X size={18} />}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
