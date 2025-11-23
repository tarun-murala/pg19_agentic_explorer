const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'

export async function POST(request: Request) {
  const payload = await request.json()
  const res = await fetch(`${ORCHESTRATOR_URL}/chat/query/stream`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok || !res.body) {
    const text = await res.text()
    return new Response(text || 'Stream failed', { status: res.status || 500 })
  }

  return new Response(res.body, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
