'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import Image from 'next/image'

export default function AdminLoginPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check for existing session
  useEffect(() => {
    fetch('/api/auth/session')
      .then(res => res.json())
      .then(data => {
        if (data.user) {
          router.push('/admin')
        }
      })
      .catch(() => {})
  }, [router])

  // Check for error in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const errorParam = params.get('error')
    if (errorParam) {
      const errorMessages: Record<string, string> = {
        'invalid_state': 'Session expired. Please try again.',
        'no_code': 'Authentication failed. Please try again.',
        'token_exchange': 'Failed to authenticate with Google.',
        'user_info': 'Failed to get user information.',
        'unauthorized': 'You are not authorized to access the admin area.',
        'callback_error': 'Authentication failed. Please try again.',
      }
      setError(errorMessages[errorParam] || `Authentication error: ${errorParam}`)
    }
  }, [])

  const handleSignIn = () => {
    setIsLoading(true)
    setError(null)
    // Use custom OAuth endpoint
    window.location.href = '/api/auth/google'
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="bg-navy-charcoal/50 rounded-2xl p-8 max-w-md w-full text-center">
        <Image
          src="/2nd_half_faith_icon_1024x1024.png"
          alt="2nd half faith"
          width={80}
          height={80}
          className="mx-auto mb-6 rounded-lg"
        />
        <h1 className="text-2xl font-serif text-accent-beige mb-2">
          Admin Login
        </h1>
        <p className="text-cream/70 mb-6">
          Sign in with your authorized Google account to access the admin dashboard.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleSignIn}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-white text-gray-800 rounded-lg hover:bg-gray-100 transition-colors font-medium disabled:opacity-50"
        >
          <svg viewBox="0 0 24 24" className="w-5 h-5">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          {isLoading ? 'Redirecting...' : 'Sign in with Google'}
        </button>
        <p className="text-cream/50 text-sm mt-4">
          Only authorized administrators can access this area.
        </p>
      </div>
    </div>
  )
}
