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
            <span className="text-accent-beige font-serif">2nd half faith</span> started with
            a simple belief: AI and social media can be used for good.
          </p>

          <p>
            I&apos;m a Christian in the second half of life, and like many of you, I&apos;m working
            every day to strengthen my relationship with Jesus. Some days that feels easy.
            Other days, life gets heavy — health scares, losing people we love, watching
            our kids navigate a world we barely recognize, wondering what comes next.
          </p>

          <p>
            I wanted a way to share that journey honestly. Not to preach, but to pray
            alongside others who feel the same things I do. So I built this — a daily
            prayer paired with Scripture, spoken from the heart of someone who&apos;s walking
            the same road.
          </p>

          <p>
            Every prayer is crafted for the real questions and emotions that come with
            this season of life. The kind of prayers you&apos;d whisper on a hard morning or
            hold onto when you can&apos;t find the words yourself.
          </p>

          <p>
            My hope is simple: that these prayers meet you where you are and remind you
            that God is still speaking into the second half of your story.
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
