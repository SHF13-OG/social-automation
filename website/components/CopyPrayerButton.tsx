'use client'

import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

interface CopyPrayerButtonProps {
  prayerText: string
}

export default function CopyPrayerButton({ prayerText }: CopyPrayerButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(prayerText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea')
      textarea.value = prayerText
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-2 px-3 py-1.5 text-sm text-accent-beige/70 hover:text-accent-beige transition-colors"
      aria-label={copied ? 'Copied' : 'Copy this prayer'}
    >
      {copied ? (
        <>
          <Check size={16} />
          <span>Copied!</span>
        </>
      ) : (
        <>
          <Copy size={16} />
          <span>Copy this prayer</span>
        </>
      )}
    </button>
  )
}
