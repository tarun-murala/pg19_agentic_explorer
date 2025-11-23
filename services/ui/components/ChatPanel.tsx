'use client'

import { FormEvent, useState } from 'react'

interface ChatPanelProps {
  onSubmit: (question: string) => Promise<void>
  disabled?: boolean
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ onSubmit, disabled }) => {
  const [question, setQuestion] = useState('')

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!question.trim()) return
    await onSubmit(question.trim())
    setQuestion('')
  }

  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-3">
        <label className="block text-sm font-medium text-slate-600">Ask PG-19</label>
        <textarea
          className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm focus:border-brand-500 focus:bg-white focus:outline-none"
          rows={3}
          placeholder="e.g., Describe how the narrator depicts the city in chapter 3"
          value={question}
          disabled={disabled}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          disabled={disabled || !question.trim()}
          className="w-full rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {disabled ? 'Running agents…' : 'Run agentic query'}
        </button>
      </form>
    </div>
  )
}
