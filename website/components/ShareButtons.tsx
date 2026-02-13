'use client'

import { Share2 } from 'lucide-react'

interface ShareButtonsProps {
  title: string
  text: string
  url?: string
}

export default function ShareButtons({ title, text, url }: ShareButtonsProps) {
  const shareUrl = url || (typeof window !== 'undefined' ? window.location.href : '')

  const shareToFacebook = () => {
    window.open(
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
      '_blank',
      'width=600,height=400'
    )
  }

  const shareToTwitter = () => {
    window.open(
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`,
      '_blank',
      'width=600,height=400'
    )
  }

  const shareNative = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title,
          text,
          url: shareUrl,
        })
      } catch (err) {
        // User cancelled or error
      }
    }
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-accent-beige/70 text-sm">Share:</span>

      {/* Facebook */}
      <button
        onClick={shareToFacebook}
        className="w-10 h-10 rounded-full bg-[#1877F2] flex items-center justify-center hover:opacity-80 transition-opacity"
        aria-label="Share on Facebook"
      >
        <svg viewBox="0 0 24 24" className="w-5 h-5 fill-white">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      </button>

      {/* X (Twitter) */}
      <button
        onClick={shareToTwitter}
        className="w-10 h-10 rounded-full bg-black flex items-center justify-center hover:opacity-80 transition-opacity"
        aria-label="Share on X"
      >
        <svg viewBox="0 0 24 24" className="w-5 h-5 fill-white">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      </button>

      {/* TikTok */}
      <a
        href="https://www.tiktok.com/@2ndhalf_faith"
        target="_blank"
        rel="noopener noreferrer"
        className="w-10 h-10 rounded-full bg-black flex items-center justify-center hover:opacity-80 transition-opacity"
        aria-label="Follow on TikTok"
      >
        <svg viewBox="0 0 24 24" className="w-5 h-5 fill-white">
          <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
        </svg>
      </a>

      {/* Native Share (mobile) */}
      {typeof navigator !== 'undefined' && typeof navigator.share === 'function' && (
        <button
          onClick={shareNative}
          className="w-10 h-10 rounded-full bg-accent-beige text-navy flex items-center justify-center hover:opacity-80 transition-opacity"
          aria-label="Share"
        >
          <Share2 size={20} />
        </button>
      )}
    </div>
  )
}
