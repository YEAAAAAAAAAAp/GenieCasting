import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const formData = await req.formData()
    const backend = process.env.BACKEND_URL || 'http://localhost:8000'
    const url = new URL(req.url)
    const top_k = url.searchParams.get('top_k') || '3'
    const reference_actor = url.searchParams.get('reference_actor')
    
    // 백엔드 URL에 쿼리 파라미터 추가
    const backendUrl = new URL(`${backend}/match-actors-batch`)
    backendUrl.searchParams.set('top_k', top_k)
    if (reference_actor) {
      backendUrl.searchParams.set('reference_actor', reference_actor)
    }
    
    const resp = await fetch(backendUrl.toString(), {
      method: 'POST',
      body: formData,
    })
    const data = await resp.json()
    return NextResponse.json(data, { status: resp.status })
  } catch (e: any) {
    return NextResponse.json({ detail: e?.message || 'Proxy error' }, { status: 500 })
  }
}
