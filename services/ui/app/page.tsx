'use client'

import { MouseEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { AgentTimeline } from '../components/AgentTimeline'
import { ChatPanel } from '../components/ChatPanel'
import { DatasetStatus } from '../components/DatasetStatus'
import { KGWidget } from '../components/KGWidget'
import { ChatResponse, ConversationTurn, HistoryEntry, TraceStep } from '../types'

async function fetchHistory(): Promise<HistoryEntry[]> {
  const res = await fetch('/api/history', { cache: 'no-store' })
  if (!res.ok) {
    return []
  }
  return res.json()
}

async function fetchTrace(conversationId: string): Promise<ChatResponse> {
  const res = await fetch(`/api/trace/${conversationId}`)
  if (!res.ok) {
    throw new Error('Unable to load trace')
  }
  const data = await res.json()
  return {
    conversation_id: data.id,
    answer: data.answer,
    citations: data.citations ?? [],
    trace: data.trace ?? [],
  }
}

async function downloadTrace(conversationId: string) {
  const res = await fetch(`/api/trace/${conversationId}`)
  if (!res.ok) {
    throw new Error('Trace not found')
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `trace-${conversationId}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function streamChat(question: string, onEvent: (event: any) => void) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!res.ok || !res.body) {
    throw new Error((await res.text()) || 'Failed to stream agents')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const chunk = buffer.slice(0, boundary).trim()
      buffer = buffer.slice(boundary + 2)
      if (chunk.startsWith('data:')) {
        try {
          const payload = JSON.parse(chunk.replace(/^data:\s*/, ''))
          onEvent(payload)
        } catch (err) {
          console.error('Failed to parse event', err)
        }
      }
      boundary = buffer.indexOf('\n\n')
    }
  }
}

export default function HomePage() {
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [uploadDetails, setUploadDetails] = useState<any | null>(null)

  useEffect(() => {
    setLoadingHistory(true)
    fetchHistory()
      .then((entries) => {
        setTurns(
          entries.map((entry) => ({
            id: entry.id,
            conversationId: entry.id,
            question: entry.question,
            status: 'complete',
            createdAt: entry.created_at,
            response: {
              conversation_id: entry.id,
              answer: entry.answer,
              citations: entry.citations ?? [],
              trace: [],
            },
          }))
        )
      })
      .finally(() => setLoadingHistory(false))
  }, [])

  useEffect(() => {
    if (!selectedId && turns.length > 0) {
      setSelectedId(turns[turns.length - 1].id)
    }
  }, [turns, selectedId])

  const activeTurn = useMemo(() => turns.find((turn) => turn.id === selectedId), [turns, selectedId])
  const activeTrace = activeTurn?.response?.trace

  useEffect(() => {
    const loadTraceIfNeeded = async () => {
      if (!activeTurn || activeTurn.status !== 'complete') return
      if (!activeTurn.response || (activeTurn.response.trace && activeTurn.response.trace.length > 0)) return
      if (!activeTurn.conversationId) return
      try {
        const trace = await fetchTrace(activeTurn.conversationId)
        setTurns((prev) =>
          prev.map((turn) =>
            turn.id === activeTurn.id
              ? {
                  ...turn,
                  response: trace,
                }
              : turn
          )
        )
      } catch (err) {
        console.error(err)
      }
    }
    loadTraceIfNeeded()
  }, [activeTurn])

  const kgFromTrace = useMemo(() => {
    const kgStep = activeTrace?.find((step) => step.agent === 'KGContextAgent')
    const output = kgStep?.output as { entities?: any[]; relations?: any[] } | undefined
    return {
      entities: output?.entities ?? [],
      relations: output?.relations ?? [],
    }
  }, [activeTrace])

  const isRunning = turns.some((turn) => turn.status === 'pending')

  const updateTrace = useCallback((turnId: string, traceStep: TraceStep) => {
    setTurns((prev) =>
      prev.map((turn) => {
        if (turn.id !== turnId) return turn
        const existingTrace = turn.response?.trace ?? []
        return {
          ...turn,
          response: {
            conversation_id: turn.response?.conversation_id || '',
            answer: turn.response?.answer || '',
            citations: turn.response?.citations || [],
            trace: [...existingTrace, traceStep],
          },
        }
      })
    )
  }, [])

  const handleSubmit = async (question: string) => {
    const localId = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString()
    setTurns((prev) => [
      ...prev,
      {
        id: localId,
        question,
        status: 'pending',
        response: { conversation_id: '', answer: '', citations: [], trace: [] },
      },
    ])
    setSelectedId(localId)

    try {
      await streamChat(question, (event) => {
        if (process.env.NODE_ENV !== 'production') {
          console.debug('[streamChat:event]', event)
        }
        if (event.type === 'step' && event.payload) {
          updateTrace(localId, event.payload as TraceStep)
        } else if (event.type === 'final' && event.payload) {
          const conversationId = event.payload.conversation_id
          setTurns((prev) =>
            prev.map((turn) =>
              turn.id === localId
                ? {
                    ...turn,
                    id: conversationId || turn.id,
                    status: 'complete',
                    conversationId,
                    createdAt: new Date().toISOString(),
                    response: event.payload as ChatResponse,
                  }
                : turn
            )
          )
          if (conversationId) {
            setSelectedId((current) => (current === localId ? conversationId : current))
          }
        } else if (event.type === 'error') {
          setTurns((prev) =>
            prev.map((turn) =>
              turn.id === localId
                ? { ...turn, status: 'error', error: event.message || 'Agent pipeline failed' }
                : turn
            )
          )
        }
      })
    } catch (err) {
      console.error('[streamChat] failed', err)
      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === localId
            ? { ...turn, status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
            : turn
        )
      )
    }
  }

  const handleDownload = async (turn: ConversationTurn, e: MouseEvent) => {
    e.stopPropagation()
    const id = turn.conversationId || turn.response?.conversation_id
    if (!id) return
    try {
      await downloadTrace(id)
    } catch (err) {
      console.error(err)
    }
  }

  const handleUpload = async (file: File) => {
    setUploading(true)
    setUploadError(null)
    setUploadMessage(null)
    setUploadDetails(null)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: formData })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || 'Upload failed')
      }
      setUploadMessage(`Ingested ${file.name}`)
      setUploadDetails(data.ingestion)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header className="rounded-3xl bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-brand-600">PG19 Agentic Explorer</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Ask PG-19 with full agent trace transparency</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
          Run a question through the Analyzer, RAG Retrieval, KG Context, and Answer agents. Review the end-to-end
          reasoning, citations, and knowledge graph visualization for every turn.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <div className="space-y-4">
          <DatasetStatus />
          <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <header className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-brand-600">Upload & Ingest</p>
                <p className="text-xs text-slate-500">Upload a PG-19 .txt file to trigger ingestion.</p>
              </div>
            </header>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              <label
                className="flex w-full cursor-pointer items-center justify-between rounded-xl border border-dashed border-slate-300 px-3 py-3 text-sm font-semibold text-slate-700 hover:border-brand-200"
              >
                <span>{uploading ? 'Uploading…' : 'Choose a .txt file'}</span>
                <input
                  type="file"
                  accept=".txt"
                  className="hidden"
                  disabled={uploading}
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) {
                      handleUpload(file)
                      e.target.value = ''
                    }
                  }}
                />
              </label>
              {uploadMessage && <p className="text-emerald-600">{uploadMessage}</p>}
              {uploadDetails && (
                <p className="text-xs text-slate-500">
                  Book #{uploadDetails?.book?.id}: {uploadDetails?.book?.title} ({uploadDetails?.chunks?.length || 0} chunks)
                </p>
              )}
              {uploadError && <p className="text-xs text-red-600">{uploadError}</p>}
              <p className="text-xs text-slate-500">
                Files are stored in the shared dataset directory and sent to the ingestion service automatically.
              </p>
            </div>
          </section>
          <ChatPanel onSubmit={handleSubmit} disabled={isRunning} />
          <section className="space-y-3 rounded-2xl bg-white p-4 shadow-sm">
            <header className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-brand-600">Conversation</h2>
              {isRunning && <span className="text-xs text-slate-500">Running agents…</span>}
            </header>
            {loadingHistory && turns.length === 0 ? (
              <p className="text-sm text-slate-500">Loading history…</p>
            ) : turns.length === 0 ? (
              <p className="text-sm text-slate-500">No queries yet. Ask something to begin.</p>
            ) : (
              <div className="space-y-3">
                {turns.map((turn) => (
                  <button
                    key={turn.id}
                    onClick={() => setSelectedId(turn.id)}
                    className={`w-full rounded-2xl border p-4 text-left transition ${
                      selectedId === turn.id
                        ? 'border-brand-200 bg-brand-50'
                        : 'border-slate-100 bg-slate-50 hover:border-brand-100'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-800">Q: {turn.question}</p>
                      {turn.conversationId && (
                        <button
                          onClick={(e) => handleDownload(turn, e)}
                          className="text-xs font-semibold text-brand-600 hover:underline"
                        >
                          Download trace
                        </button>
                      )}
                    </div>
                    {turn.createdAt && (
                      <p className="text-xs text-slate-400">{new Date(turn.createdAt).toLocaleString()}</p>
                    )}
                    {turn.status === 'pending' && <p className="text-xs text-slate-500">Running agents…</p>}
                    {turn.status === 'error' && <p className="text-xs text-red-500">{turn.error || 'Agent orchestration failed'}</p>}
                    {turn.status === 'complete' && turn.response && (
                      <div className="mt-2 space-y-2 text-sm text-slate-600">
                        <p>{turn.response.answer}</p>
                        {turn.response.citations.length > 0 && (
                          <p className="text-xs text-slate-500">
                            Citations: {turn.response.citations.map((c) => `#${c}`).join(', ')}
                          </p>
                        )}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="space-y-4">
          <KGWidget entities={kgFromTrace.entities} relations={kgFromTrace.relations} />
          {activeTurn?.response && (
            <div className="rounded-2xl bg-white p-4 text-sm shadow-sm">
              <p className="text-sm font-semibold text-brand-600">Answer Summary</p>
              <p className="mt-2 text-slate-700">{activeTurn.response.answer || 'Awaiting response…'}</p>
              {activeTurn.response.citations.length > 0 && (
                <p className="mt-2 text-xs text-slate-500">
                  Citations: {activeTurn.response.citations.map((c) => `#${c}`).join(', ')}
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-brand-600">Agent Timeline</h2>
        <AgentTimeline trace={activeTrace} />
      </section>
    </main>
  )
}
