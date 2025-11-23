import { NextResponse } from 'next/server'

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'

export async function GET() {
  const res = await fetch(`${ORCHESTRATOR_URL}/history`, { cache: 'no-store' })
  if (!res.ok) {
    const text = await res.text()
    return NextResponse.json({ error: text || 'Failed to load history' }, { status: res.status })
  }
  const data = await res.json()
  return NextResponse.json(data)
}
