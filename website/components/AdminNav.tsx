'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  Palette,
  BookOpen,
  ListOrdered,
  Calendar,
  MessageSquare,
  TestTube2,
  LogOut,
  Home,
} from 'lucide-react'

const navItems = [
  { href: '/admin', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/admin/themes', label: 'Themes', icon: Palette },
  { href: '/admin/prayers', label: 'Prayers', icon: BookOpen },
  { href: '/admin/lineup', label: 'Lineup', icon: ListOrdered },
  { href: '/admin/schedule', label: 'Schedule', icon: Calendar },
  { href: '/admin/chat', label: 'AI Chat', icon: MessageSquare },
  { href: '/admin/tests', label: 'Tests', icon: TestTube2 },
]

export default function AdminNav() {
  const pathname = usePathname()
  const router = useRouter()

  const handleSignOut = async () => {
    // Clear the session cookie by calling logout endpoint
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
  }

  return (
    <nav className="bg-navy-charcoal border-b border-accent-beige/20">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/admin" className="flex items-center gap-2">
            <span className="text-accent-beige font-serif text-lg">2nd half faith</span>
            <span className="text-cream/50 text-sm">Admin</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-accent-beige/20 text-accent-beige'
                      : 'text-cream/70 hover:text-cream hover:bg-navy/50'
                  }`}
                >
                  <Icon size={18} />
                  <span className="hidden md:inline">{item.label}</span>
                </Link>
              )
            })}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-cream/70 hover:text-cream hover:bg-navy/50 transition-colors"
            >
              <Home size={18} />
              <span className="hidden sm:inline">View Site</span>
            </Link>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-cream/70 hover:text-cream hover:bg-navy/50 transition-colors"
            >
              <LogOut size={18} />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
