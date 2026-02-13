'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          history: messages,
        }),
      })

      if (!res.ok) throw new Error('Failed to get response')

      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-serif text-accent-beige">AI Assistant</h1>
        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="text-sm text-cream/50 hover:text-cream transition-colors"
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="w-16 h-16 text-accent-beige/30 mb-4" />
            <h2 className="text-xl font-serif text-accent-beige mb-2">
              How can I help?
            </h2>
            <p className="text-cream/50 max-w-md">
              Ask me about engagement trends, CTA improvements, content suggestions, or posting strategies.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-6">
              {[
                'Analyze my engagement trends',
                'Suggest better CTAs',
                'Best posting times?',
                'Help with content ideas',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="px-4 py-2 bg-navy-charcoal/50 text-cream/70 rounded-lg text-sm hover:bg-navy-charcoal hover:text-cream transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-accent-beige/20 flex items-center justify-center flex-shrink-0">
                  <Bot size={18} className="text-accent-beige" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-accent-beige text-navy'
                    : 'bg-navy-charcoal/50 text-cream'
                }`}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content}
                </p>
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-accent-beige flex items-center justify-center flex-shrink-0">
                  <User size={18} className="text-navy" />
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-accent-beige/20 flex items-center justify-center flex-shrink-0">
              <Bot size={18} className="text-accent-beige" />
            </div>
            <div className="bg-navy-charcoal/50 rounded-2xl px-4 py-3">
              <Loader size={18} className="text-accent-beige animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about engagement, content, or strategy..."
          className="flex-1 bg-navy-charcoal border border-accent-beige/30 text-cream rounded-xl px-4 py-3 focus:outline-none focus:border-accent-beige placeholder:text-cream/30"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="px-6 py-3 bg-accent-beige text-navy rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  )
}
