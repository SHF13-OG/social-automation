import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ensureDb, getPrayerByDate, getAvailableDates } from '@/lib/db'
import AudioPlayer from '@/components/AudioPlayer'
import ShareButtons from '@/components/ShareButtons'

export const dynamic = 'force-dynamic'

interface Props {
  params: Promise<{ date: string }>
}

export default async function PrayerArchivePage({ params }: Props) {
  const { date } = await params

  // Validate date format (YYYY-MM-DD)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    notFound()
  }

  await ensureDb()
  const prayer = getPrayerByDate(date)

  if (!prayer) {
    notFound()
  }

  const formattedDate = new Date(date + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  // Get available dates for navigation
  const availableDates = getAvailableDates()
  const currentIndex = availableDates.indexOf(date)
  const prevDate = currentIndex < availableDates.length - 1 ? availableDates[currentIndex + 1] : null
  const nextDate = currentIndex > 0 ? availableDates[currentIndex - 1] : null

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="p-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <Image
            src="/2nd_half_faith_icon_1024x1024.png"
            alt="2nd half faith"
            width={48}
            height={48}
            className="rounded-lg"
          />
          <span className="text-accent-beige font-serif text-xl hidden sm:inline">
            2nd half faith
          </span>
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/" className="text-cream/70 hover:text-cream transition-colors">
            Today
          </Link>
          <Link href="/about" className="text-cream/70 hover:text-cream transition-colors">
            About
          </Link>
        </nav>
      </header>

      {/* Main Content */}
      <div className="max-w-2xl mx-auto px-6 py-8">
        {/* Date Navigation */}
        <div className="flex items-center justify-between mb-4">
          {prevDate ? (
            <Link
              href={`/prayer/${prevDate}`}
              className="text-accent-beige/70 hover:text-accent-beige transition-colors"
            >
              &larr; Previous
            </Link>
          ) : (
            <span />
          )}
          <p className="text-accent-beige/70 text-center">{formattedDate}</p>
          {nextDate ? (
            <Link
              href={`/prayer/${nextDate}`}
              className="text-accent-beige/70 hover:text-accent-beige transition-colors"
            >
              Next &rarr;
            </Link>
          ) : (
            <span />
          )}
        </div>

        {/* Theme Badge */}
        <div className="flex justify-center mb-6">
          <span className="px-4 py-1 bg-accent-beige/20 text-accent-beige rounded-full text-sm">
            {prayer.theme_name}
          </span>
        </div>

        {/* Verse Reference */}
        <h1 className="text-3xl sm:text-4xl font-serif text-accent-beige text-center mb-4">
          {prayer.verse_ref}
        </h1>

        {/* Verse Text */}
        <blockquote className="text-xl sm:text-2xl text-cream text-center italic mb-8 leading-relaxed">
          &ldquo;{prayer.verse_text}&rdquo;
        </blockquote>

        {/* Divider */}
        <div className="flex items-center justify-center mb-8">
          <div className="h-px bg-accent-beige/30 flex-1" />
          <span className="px-4 text-accent-beige/50">&#10022;</span>
          <div className="h-px bg-accent-beige/30 flex-1" />
        </div>

        {/* Prayer Text */}
        <div className="bg-navy-charcoal/50 rounded-2xl p-6 sm:p-8 mb-8">
          <h2 className="text-lg text-accent-beige mb-4 font-serif">Prayer</h2>
          <p className="prayer-text text-cream/90 text-lg leading-loose">
            {prayer.prayer_text}
          </p>
        </div>

        {/* Audio Player */}
        {prayer.audio_path && (
          <div className="mb-8">
            <AudioPlayer
              src={`/api/audio/${prayer.prayer_id}`}
              duration={prayer.duration_sec || undefined}
            />
          </div>
        )}

        {/* Share Buttons */}
        <div className="flex justify-center mb-8">
          <ShareButtons
            title={`${prayer.verse_ref} | 2nd half faith`}
            text={`"${prayer.verse_text}" - ${prayer.verse_ref}\n\nFind daily encouragement at 2ndhalffaith.com`}
          />
        </div>

        {/* Archive Link */}
        <div className="text-center">
          <Link
            href="/prayer/archive"
            className="text-accent-beige/70 hover:text-accent-beige transition-colors"
          >
            View All Prayers &rarr;
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="p-6 text-center text-cream/50 text-sm">
        <p>&copy; {new Date().getFullYear()} 2nd half faith. All rights reserved.</p>
        <div className="flex justify-center gap-4 mt-2">
          <Link href="/PRIVACY.md" className="hover:text-cream transition-colors">
            Privacy
          </Link>
          <Link href="/TERMS.md" className="hover:text-cream transition-colors">
            Terms
          </Link>
        </div>
      </footer>
    </main>
  )
}
