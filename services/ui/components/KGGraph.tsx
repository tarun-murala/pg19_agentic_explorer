'use client'

import { useEffect, useRef } from 'react'
import { DataSet, Network } from 'vis-network/standalone'

type GraphNode = {
  id: string
  label: string
  title?: string
  shape?: string
  size?: number
  color?: string
}

type GraphEdge = {
  id: string
  from: string
  to: string
  label?: string
  arrows?: string
  color?: { color: string }
  font?: { size: number; align: string }
}

interface Props {
  entities: { name: string; type?: string }[]
  relations: { source: string; target: string; type?: string }[]
}

export const KGGraph: React.FC<Props> = ({ entities, relations }) => {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const nodes = new DataSet<GraphNode>(
      entities.map((entity, idx) => ({
        id: entity.name || String(idx),
        label: entity.name,
        title: `${entity.name}\n${entity.type || 'unknown'}`,
        shape: 'dot',
        size: 18,
        color: entity.type === 'person' ? '#7c3aed' : '#6366f1',
      }))
    )
    const edges = new DataSet<GraphEdge>(
      relations.map((rel, idx) => ({
        id: `${rel.source}-${rel.target}-${idx}`,
        from: rel.source,
        to: rel.target,
        label: rel.type || 'relates',
        arrows: 'to',
        color: { color: '#cbd5f5' },
        font: { size: 10, align: 'horizontal' },
      }))
    )
    const network = new Network(
      containerRef.current,
      { nodes, edges },
      {
        autoResize: true,
        physics: { stabilization: true },
        interaction: { hover: true },
        nodes: {
          font: { color: '#0f172a', size: 12 },
        },
        edges: {
          smooth: true,
        },
      }
    )
    return () => {
      network.destroy()
    }
  }, [entities, relations])

  return <div ref={containerRef} className="h-64 w-full" />
}
