import Image from 'next/image'
import Link from 'next/link'
import { getRecentPrayers } from '@/lib/db'

export const dynamic = 'force-dynamic'

export default function PrayerArchivePage() {
  const prayers = getRecentPrayers(100)

  // Group prayers by month
  const prayersByMonth = prayers.reduce((acc, prayer) => {
    const date = new Date(prayer.created_at)
    const monthKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
    if (!acc[monthKey]) {
      acc[monthKey] = []
    }
    acc[monthKey].push(prayer)
    return acc
  }, {} as Record<string, typeof prayers>)

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
        <h1 className="text-3xl sm:text-4xl font-serif text-accent-beige text-center mb-8">
          Prayer Archive
        </h1>

        {prayers.length === 0 ? (
          <p className="text-center text-cream/70">No prayers available yet.</p>
        ) : (
          <div className="space-y-8">
            {Object.entries(prayersByMonth).map(([month, monthPrayers]) => (
              <div key={month}>
                <h2 className="text-xl font-serif text-accent-beige/70 mb-4 border-b border-accent-beige/20 pb-2">
                  {month}
                </h2>
                <div className="space-y-3">
                  {monthPrayers.map((prayer) => {
                    const date = prayer.created_at.split('T')[0]
                    const formattedDate = new Date(prayer.created_at).toLocaleDateString('en-US', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                    })

                    return (
                      <Link
                        key={prayer.prayer_id}
                        href={`/prayer/${date}`}
                        className="block bg-navy-charcoal/30 hover:bg-navy-charcoal/50 rounded-lg p-4 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-accent-beige font-serif">
                                {prayer.verse_ref}
                              </span>
                              <span className="text-xs px-2 py-0.5 bg-accent-beige/20 text-accent-beige/80 rounded-full">
                                {prayer.theme_name}
                              </span>
                            </div>
                            <p className="text-cream/70 text-sm truncate">
                              &ldquo;{prayer.verse_text}&rdquo;
                            </p>
                          </div>
                          <span className="text-cream/50 text-sm whitespace-nowrap">
                            {formattedDate}
                          </span>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
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
