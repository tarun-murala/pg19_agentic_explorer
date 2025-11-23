export type TraceStep = {
  agent: string
  input: Record<string, unknown>
  output: Record<string, unknown>
  started_at: string
  finished_at: string
}

export type ChatResponse = {
  conversation_id: string
  answer: string
  trace: TraceStep[]
  citations: number[]
}

export type ConversationTurn = {
  id: string
  question: string
  response?: ChatResponse
  status: 'pending' | 'complete' | 'error'
  error?: string
  createdAt?: string
  conversationId?: string
}

export type HistoryEntry = {
  id: string
  question: string
  answer: string
  citations: number[]
  created_at: string
}
