import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const formData = await req.formData()
    const backend = process.env.BACKEND_URL
    
    // 환경변수 검증
    if (!backend) {
      console.error('[API Route] BACKEND_URL environment variable is not set')
      return NextResponse.json(
        { detail: 'Server configuration error: BACKEND_URL not set. Please configure environment variables in Vercel dashboard.' },
        { status: 500 }
      )
    }
    
    const url = new URL(req.url)
    const top_k = url.searchParams.get('top_k') || '3'
    const resp = await fetch(`${backend}/match-actors?top_k=${encodeURIComponent(top_k)}`, { method: 'POST', body: formData })
    const data = await resp.json()
    return NextResponse.json(data, { status: resp.status })
  } catch (e: any) {
    return NextResponse.json({ detail: e?.message || 'Proxy error' }, { status: 500 })
  }
}
