'use client'

import dynamic from 'next/dynamic'
import { Suspense } from 'react'

const KGGraph = dynamic(() => import('./KGGraph').then((mod) => mod.KGGraph), { ssr: false })

interface KGWidgetProps {
  entities: { name: string; type?: string; description?: string; mentions?: number }[]
  relations: { source: string; target: string; type?: string; description?: string }[]
}

export const KGWidget: React.FC<KGWidgetProps> = ({ entities, relations }) => {
  const hasData = entities.length > 0 || relations.length > 0
  if (!hasData) {
    return (
      <div className="rounded-2xl bg-white p-4 text-sm text-slate-500 shadow-sm">
        KG entities + relations appear once the KG agent runs.
      </div>
    )
  }
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-brand-600">Knowledge Graph Snapshot</h3>
      <div className="mt-4 space-y-4 text-sm">
        <div>
          <p className="font-semibold text-slate-600">Entities</p>
          <ul className="mt-2 space-y-2">
            {entities.slice(0, 8).map((entity) => (
              <li key={entity.name} className="rounded-xl border border-slate-100 bg-slate-50 p-2">
                <p className="text-sm font-medium text-slate-800">{entity.name}</p>
                <p className="text-xs text-slate-500">
                  {entity.type || 'unknown'}
                  {typeof entity.mentions === 'number' ? ` · mentions ${entity.mentions}` : ''}
                </p>
                {entity.description && <p className="mt-1 text-xs text-slate-500">{entity.description}</p>}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-semibold text-slate-600">Relations</p>
          <ul className="mt-2 space-y-2">
            {relations.slice(0, 8).map((rel, idx) => (
              <li key={`${rel.source}-${rel.target}-${idx}`} className="rounded-xl border border-slate-100 bg-slate-50 p-2">
                <p className="text-sm text-slate-800">
                  <span className="font-semibold">{rel.source}</span>
                  <span className="mx-1 text-slate-400">{rel.type || 'related_to'}</span>
                  <span className="font-semibold">{rel.target}</span>
                </p>
                {rel.description && <p className="mt-1 text-xs text-slate-500">{rel.description}</p>}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-semibold text-slate-600">Interactive View</p>
          <div className="mt-2 rounded-xl border border-slate-100 bg-slate-50 p-2">
            <Suspense fallback={<p className="text-xs text-slate-500">Loading graph…</p>}>
              <KGGraph entities={entities} relations={relations} />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  )
}
