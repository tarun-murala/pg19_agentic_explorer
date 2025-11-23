'use client'

import { useEffect, useState } from 'react'

interface DatasetStatusState {
  exists: boolean
  path?: string
  message?: string
}

export const DatasetStatus: React.FC = () => {
  const [state, setState] = useState<DatasetStatusState>({ exists: false })
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const checkDataset = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/dataset', { cache: 'no-store' })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setState({ exists: data.exists, path: data.path })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to check dataset')
    } finally {
      setLoading(false)
    }
  }

  const downloadDataset = async () => {
    setDownloading(true)
    setError(null)
    try {
      const res = await fetch('/api/dataset', { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setState({ exists: true, path: data.path, message: data.message })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dataset download failed')
    } finally {
      setDownloading(false)
    }
  }

  useEffect(() => {
    checkDataset()
  }, [])

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-brand-600">PG-19 Dataset</p>
          <p className="text-xs text-slate-500">Required for ingestion. Path: {state.path || 'detecting…'}</p>
        </div>
        <button
          onClick={checkDataset}
          className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:border-brand-200"
          disabled={loading}
        >
          {loading ? 'Checking…' : 'Recheck'}
        </button>
      </div>
      <div className="mt-3 text-sm">
        {state.exists ? (
          <p className="text-emerald-600">Dataset detected ✓</p>
        ) : (
          <div>
            <p className="text-amber-600">Dataset missing. Download from Hugging Face.</p>
            <button
              onClick={downloadDataset}
              className="mt-2 rounded-xl bg-brand-600 px-4 py-2 text-xs font-semibold text-white disabled:bg-slate-300"
              disabled={downloading}
            >
              {downloading ? 'Downloading… (may take a while)' : 'Download dataset'}
            </button>
          </div>
        )}
        {state.message && <p className="mt-2 text-xs text-slate-500">{state.message}</p>}
        {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      </div>
    </div>
  )
}
