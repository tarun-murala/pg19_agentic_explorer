import { TraceStep } from '../types'

interface Props {
  trace?: TraceStep[]
}

const formatTime = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

export const AgentTimeline: React.FC<Props> = ({ trace }) => {
  if (!trace || trace.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-4 text-sm text-slate-500 shadow-sm">
        Agent trace will appear here after you run a query.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {trace.map((step) => (
        <div key={`${step.agent}-${step.started_at}`} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-brand-600">{step.agent}</p>
            <span className="text-xs text-slate-500">
              {formatTime(step.started_at)} → {formatTime(step.finished_at)}
            </span>
          </div>
          <div className="mt-3 grid gap-3 text-xs">
            <div>
              <p className="font-semibold text-slate-500">Input</p>
              <pre className="mt-1 overflow-x-auto rounded-xl bg-slate-50 p-2 text-slate-700">
                {JSON.stringify(step.input, null, 2)}
              </pre>
            </div>
            <div>
              <p className="font-semibold text-slate-500">Output</p>
              <pre className="mt-1 overflow-x-auto rounded-xl bg-slate-50 p-2 text-slate-700">
                {JSON.stringify(step.output, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
