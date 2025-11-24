import { NextResponse } from 'next/server'

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'
const buildTraceId = () => crypto.randomUUID()

export async function POST(request: Request) {
  const payload = await request.json()
  const traceId = request.headers.get('x-trace-id') || buildTraceId()

  console.log('[api/chat] -> orchestrator', { traceId, payload })
  const res = await fetch(`${ORCHESTRATOR_URL}/chat/query`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-trace-id': traceId,
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const error = await res.text()
    console.error('[api/chat] orchestrator error', { traceId, status: res.status, error })
    return NextResponse.json({ error, traceId }, { status: res.status })
  }

  const data = await res.json()
  console.log('[api/chat] <- orchestrator', { traceId })
  return NextResponse.json({ ...data, traceId })
}
