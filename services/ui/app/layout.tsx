import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PG19 Agentic Explorer',
  description: 'Local agentic RAG UI over PG-19',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  )
}
