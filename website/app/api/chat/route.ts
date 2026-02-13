import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'

export const dynamic = 'force-dynamic'

// Cloudflare Workers AI via REST API
async function callCloudflareAI(prompt: string): Promise<string> {
  const accountId = process.env.CLOUDFLARE_ACCOUNT_ID
  const apiToken = process.env.CLOUDFLARE_API_TOKEN

  if (!accountId || !apiToken) {
    throw new Error('Cloudflare AI credentials not configured')
  }

  const response = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/run/@cf/meta/llama-3.1-8b-instruct`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        max_tokens: 1000,
      }),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Cloudflare AI error: ${error}`)
  }

  const data = await response.json()
  return data.result?.response || 'Sorry, I could not generate a response.'
}

export async function POST(request: NextRequest) {
  const session = await getSession()

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const { message, history } = await request.json()

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 })
    }

    const systemPrompt = `You are an AI assistant helping manage a faith-based TikTok account called "2nd half faith" that creates daily prayer content for Christians aged 45+.

Your role is to:
1. Analyze engagement trends and provide actionable recommendations
2. Suggest improvements to calls-to-action (CTAs)
3. Help craft content overrides when requested
4. Answer questions about the publishing pipeline
5. Provide posting time recommendations based on engagement patterns

Be concise, practical, and focused on improving engagement. When suggesting content changes, always maintain the reverent, encouraging tone appropriate for the target audience.

Note: Analytics data is not yet connected. Please provide general best practices and guidance.`

    // Build conversation history
    const conversationHistory = (history || []).map((msg: { role: string; content: string }) =>
      `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
    ).join('\n')

    const historySection = conversationHistory
      ? `Previous conversation:\n${conversationHistory}\n`
      : ''

    const fullPrompt = `${systemPrompt}\n\n${historySection}User: ${message}\n\nAssistant:`

    const response = await callCloudflareAI(fullPrompt)

    return NextResponse.json({ response })
  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to process chat' },
      { status: 500 }
    )
  }
}
