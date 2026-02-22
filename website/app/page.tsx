import Image from 'next/image'
import Link from 'next/link'
import { ensureDb, getTodaysPrayer, getRecentPrayers } from '@/lib/db'
import AudioPlayer from '@/components/AudioPlayer'
import ShareButtons from '@/components/ShareButtons'
import CopyPrayerButton from '@/components/CopyPrayerButton'

export const dynamic = 'force-dynamic'

export default async function Home() {
  await ensureDb()
  const prayer = getTodaysPrayer()

  if (!prayer) {
    return (
      <main className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
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
          </div>
          <nav className="flex items-center gap-4">
            <Link href="/" className="text-accent-beige hover:text-accent-beige transition-colors">
              Today&apos;s Prayer
            </Link>
            <Link href="/about" className="text-cream/70 hover:text-cream transition-colors">
              About
            </Link>
          </nav>
        </header>

        {/* Hero */}
        <div className="flex-1 flex flex-col items-center justify-center p-6">
          <Image
            src="/2nd_half_faith_icon_1024x1024.png"
            alt="2nd half faith"
            width={200}
            height={200}
            className="mb-8"
          />
          <h1 className="text-3xl sm:text-4xl font-serif text-accent-beige mb-4 text-center">
            2nd half faith
          </h1>
          <p className="text-cream/70 text-center max-w-md text-lg leading-relaxed">
            Daily prayers and devotionals for Christians in the second half of life.
          </p>
          <a
            href="https://www.tiktok.com/@2ndhalf_faith"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-8 px-6 py-3 bg-accent-beige text-navy rounded-lg hover:opacity-90 transition-opacity"
          >
            Follow us on TikTok
          </a>
          <div className="mt-8 flex gap-4">
            <Link href="/about" className="text-accent-beige/70 hover:text-accent-beige transition-colors">
              About
            </Link>
            <Link href="/admin" className="text-accent-beige/70 hover:text-accent-beige transition-colors">
              Admin
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

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const recentPrayers = getRecentPrayers(7)
  // Filter out today's prayer to avoid duplication
  const olderPrayers = recentPrayers.filter(p => p.prayer_id !== prayer.prayer_id).slice(0, 6)

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
          <Link href="/" className="text-accent-beige hover:text-accent-beige transition-colors">
            Today&apos;s Prayer
          </Link>
          <Link href="/about" className="text-cream/70 hover:text-cream transition-colors">
            About
          </Link>
        </nav>
      </header>

      {/* Main Content */}
      <div className="max-w-2xl mx-auto px-6 py-8">
        {/* Date */}
        <p className="text-accent-beige/70 text-center mb-2">{today}</p>

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
          <span className="px-4 text-accent-beige/50">✦</span>
          <div className="h-px bg-accent-beige/30 flex-1" />
        </div>

        {/* Prayer Text */}
        <div className="bg-navy-charcoal/50 rounded-2xl p-6 sm:p-8 mb-2">
          <h2 className="text-lg text-accent-beige mb-4 font-serif">Today&apos;s Prayer</h2>
          <p className="prayer-text text-cream/90 text-lg leading-loose">
            {prayer.prayer_text}
          </p>
        </div>

        {/* Copy Button */}
        <div className="flex justify-end mb-8">
          <CopyPrayerButton prayerText={prayer.prayer_text} />
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
            View Prayer Archive →
          </Link>
        </div>

        {/* Recent Prayers */}
        {olderPrayers.length > 0 && (
          <section className="mt-16">
            <h2 className="text-2xl font-serif text-accent-beige text-center mb-8">
              Recent Prayers
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {olderPrayers.map((p) => {
                const date = new Date(p.created_at)
                const dateStr = date.toISOString().split('T')[0]
                const formattedDate = date.toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })
                const preview = p.prayer_text.length > 60
                  ? p.prayer_text.slice(0, 60) + '...'
                  : p.prayer_text

                return (
                  <Link
                    key={p.prayer_id}
                    href={`/prayer/${dateStr}`}
                    className="block bg-navy-charcoal/50 rounded-xl p-4 hover:bg-navy-charcoal/70 transition-colors"
                  >
                    <p className="text-accent-beige/60 text-sm mb-1">{formattedDate}</p>
                    <span className="inline-block px-2 py-0.5 bg-accent-beige/20 text-accent-beige rounded-full text-xs mb-2">
                      {p.theme_name}
                    </span>
                    <p className="text-accent-beige font-serif text-sm mb-1">{p.verse_ref}</p>
                    <p className="text-cream/60 text-sm">{preview}</p>
                  </Link>
                )
              })}
            </div>
          </section>
        )}
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
