import { NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

export const runtime = 'nodejs'

const INGESTION_URL = process.env.INGESTION_URL || 'http://localhost:8001'
const DATASET_DIR = process.env.DATASET_DIR || '/data/pg19'

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const file = formData.get('file')
    if (!file || !(file instanceof Blob)) {
      return NextResponse.json({ error: 'File is required' }, { status: 400 })
    }

    const originalName = (file as any).name || 'upload.txt'
    if (!originalName.toLowerCase().endsWith('.txt')) {
      return NextResponse.json({ error: 'Only .txt files are supported' }, { status: 400 })
    }

    const safeName = originalName.replace(/[^a-zA-Z0-9._-]/g, '_')
    const targetDir = path.resolve(DATASET_DIR)
    const targetPath = path.join(targetDir, safeName)
    await fs.mkdir(targetDir, { recursive: true })
    const buf = Buffer.from(await file.arrayBuffer())
    await fs.writeFile(targetPath, buf)

    // Trigger ingestion
    const res = await fetch(`${INGESTION_URL}/ingest/book`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ file_path: targetPath, overrides: {} }),
    })

    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: text || 'Ingestion failed', path: targetPath }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json({
      message: 'Uploaded and ingested successfully',
      path: targetPath,
      ingestion: data,
    })
  } catch (err) {
    console.error('[api/upload] error', err)
    return NextResponse.json({ error: 'Upload failed' }, { status: 500 })
  }
}
