import Image from 'next/image'
import Link from 'next/link'

export default function AboutPage() {
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
            Today&apos;s Prayer
          </Link>
        </nav>
      </header>

      {/* Main Content */}
      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-serif text-accent-beige text-center mb-8">
          About 2nd half faith
        </h1>

        <div className="space-y-6 text-cream/90 text-lg leading-relaxed">
          <p>
            <span className="text-accent-beige font-serif">2nd half faith</span> provides daily
            prayers and devotionals specifically crafted for Christians navigating the second
            half of life.
          </p>

          <p>
            Whether you&apos;re facing retirement, health challenges, grief, questions about your
            legacy, or the joys and complexities of grandparenting, we believe God&apos;s Word
            speaks directly to your journey.
          </p>

          <div className="bg-navy-charcoal/50 rounded-2xl p-6 my-8">
            <h2 className="text-xl font-serif text-accent-beige mb-4">Our Themes</h2>
            <ul className="space-y-2 text-cream/80">
              <li>• <span className="text-accent-beige">Grief & Loss</span> — Finding comfort in sorrow</li>
              <li>• <span className="text-accent-beige">Retirement</span> — Embracing new purpose</li>
              <li>• <span className="text-accent-beige">Health Challenges</span> — Hope in difficulty</li>
              <li>• <span className="text-accent-beige">Faith Questions</span> — Honest doubts, deeper trust</li>
              <li>• <span className="text-accent-beige">Adult Children</span> — Letting go, staying connected</li>
              <li>• <span className="text-accent-beige">Marriage Renewal</span> — Love that lasts</li>
              <li>• <span className="text-accent-beige">Legacy</span> — What you leave behind</li>
              <li>• <span className="text-accent-beige">Grandparenting</span> — Generational blessing</li>
            </ul>
          </div>

          <p>
            Each day, we share a Scripture passage paired with a heartfelt prayer that speaks
            to the unique experiences of those 45 and older. Our content is also available
            on TikTok, where we reach thousands with encouragement and faith.
          </p>

          <div className="flex justify-center mt-8">
            <a
              href="https://www.tiktok.com/@2ndhalf_faith"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-accent-beige text-navy rounded-lg hover:opacity-90 transition-opacity font-serif text-lg"
            >
              Follow @2ndhalf_faith on TikTok
            </a>
          </div>
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
