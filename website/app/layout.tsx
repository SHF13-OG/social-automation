import type { Metadata } from 'next'
import './globals.css'
import Providers from '@/components/Providers'

export const metadata: Metadata = {
  metadataBase: new URL('https://2ndhalffaith.com'),
  title: '2nd half faith | Daily Prayer & Devotional',
  description: 'Daily prayers and devotionals for Christians in the second half of life. Find comfort, hope, and encouragement through Scripture.',
  icons: {
    icon: '/2nd_half_faith_icon_1024x1024.png',
    apple: '/2nd_half_faith_icon_1024x1024.png',
  },
  openGraph: {
    title: '2nd half faith',
    description: 'Daily prayers and devotionals for Christians 45+',
    images: ['/2nd_half_faith_icon_1024x1024.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-navy text-cream antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
