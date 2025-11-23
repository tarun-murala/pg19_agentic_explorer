import { NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)
const DATASET_DIR = process.env.DATASET_DIR
  ? path.resolve(process.cwd(), process.env.DATASET_DIR)
  : path.resolve(process.cwd(), '../..', 'data', 'pg19')
const DATASET_REPO = 'https://huggingface.co/datasets/deepmind/pg19'

async function datasetExists(): Promise<boolean> {
  try {
    await fs.access(DATASET_DIR)
    return true
  } catch {
    return false
  }
}

export async function GET() {
  const exists = await datasetExists()
  return NextResponse.json({ exists, path: DATASET_DIR })
}

export async function POST() {
  if (await datasetExists()) {
    return NextResponse.json({ message: 'Dataset already present', path: DATASET_DIR })
  }

  await fs.mkdir(path.dirname(DATASET_DIR), { recursive: true })

  const cloneCmd = `git clone ${DATASET_REPO} ${DATASET_DIR}`
  try {
    await execAsync(cloneCmd, { cwd: path.resolve(process.cwd(), '../..') })
    return NextResponse.json({ message: 'Dataset download completed', path: DATASET_DIR })
  } catch (error) {
    const err = error as { stderr?: string; stdout?: string }
    return NextResponse.json(
      {
        error: 'Failed to download dataset via git clone. Ensure git-lfs is installed.',
        details: err.stderr || err.stdout,
      },
      { status: 500 }
    )
  }
}
