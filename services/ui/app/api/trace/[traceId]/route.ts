const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'

interface Params {
  params: {
    traceId: string
  }
}

export async function GET(request: Request, { params }: Params) {
  const res = await fetch(`${ORCHESTRATOR_URL}/trace/${params.traceId}`)
  if (!res.ok || !res.body) {
    const text = await res.text()
    return new Response(text || 'Trace not found', { status: res.status })
  }

  const headers = new Headers(res.headers)
  headers.set('Content-Type', 'application/json')
  headers.set('Cache-Control', 'no-cache')
  return new Response(res.body, { headers })
}
