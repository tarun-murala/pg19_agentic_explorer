const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'
const buildTraceId = () => crypto.randomUUID()

export async function POST(request: Request) {
  const payload = await request.json()
  const traceId = request.headers.get('x-trace-id') || buildTraceId()

  console.log('[api/chat/stream] -> orchestrator', { traceId, payload })
  const res = await fetch(`${ORCHESTRATOR_URL}/chat/query/stream`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      Accept: 'text/event-stream',
      'x-trace-id': traceId,
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok || !res.body) {
    const text = await res.text()
    console.error('[api/chat/stream] orchestrator stream error', { traceId, status: res.status, text })
    return new Response(text || 'Stream failed', { status: res.status || 500 })
  }

  console.log('[api/chat/stream] <- orchestrator (stream open)', { traceId })
  return new Response(res.body, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Trace-Id': traceId,
    },
  })
}
