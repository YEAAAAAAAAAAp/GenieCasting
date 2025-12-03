import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const formData = await req.formData()
    const backend = process.env.BACKEND_URL
    
    // 환경변수 디버깅
    console.log('[DEBUG] BACKEND_URL:', backend ? 'SET' : 'NOT SET')
    console.log('[DEBUG] Full backend URL:', backend)
    
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
      signal: AbortSignal.timeout(895000), // 895초 타임아웃 (Vercel 900초보다 짧게)
    })
    
    console.log('[DEBUG] Backend response status:', resp.status)
    
    if (!resp.ok) {
      const errorText = await resp.text()
      console.error('[API Route Error]', resp.status, errorText)
      return NextResponse.json(
        { detail: `Backend error: ${resp.status} - ${errorText}` }, 
        { status: resp.status }
      )
    }
    
    const data = await resp.json()
    
    // 상대 경로 image_url을 절대 URL로 변환 (일반 모드만)
    if (data.items && Array.isArray(data.items)) {
      data.items = data.items.map((item: any) => {
        // 레퍼런스 모드는 image_url이 없으므로 변환 불필요
        if (item.results && Array.isArray(item.results)) {
          item.results = item.results.map((result: any) => {
            if (result.image_url && !result.image_url.startsWith('http')) {
              result.image_url = `${backend}${result.image_url}`
            }
            return result
          })
        }
        return item
      })
    }
    
    return NextResponse.json(data, { status: resp.status })
  } catch (e: any) {
    console.error('[API Route Exception]', e)
    return NextResponse.json({ 
      detail: e?.message || 'Proxy error',
      error: e?.toString(),
      stack: e?.stack 
    }, { status: 500 })
  }
}
