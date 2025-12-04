# ✅ 배포 전 체크리스트

**작성일**: 2025-12-05  
**목표**: 프로덕션 배포 최종 검증

---

## 🔴 필수 작업 (배포 전 완료 필수)

### 1. Vercel 환경변수 설정 ⏱️ 5분
**URL**: https://vercel.com/your-team/genie-casting/settings/environment-variables

**추가할 변수**:
```bash
# Production, Preview, Development 모두 체크
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-6JCS9PRV6E

# Production만 체크
NEXT_PUBLIC_CLARITY_PROJECT_ID=ugbnmysm9k
```

**단계**:
1. Vercel Dashboard 로그인
2. GenieCasting 프로젝트 선택
3. Settings → Environment Variables
4. 각 변수 추가 → Save
5. Deployments 탭 → 최신 배포 → Redeploy

**검증**:
- [ ] Redeploy 완료
- [ ] 프로덕션 URL에서 브라우저 콘솔 확인 → GA/Clarity 로드 확인
- [ ] 이미지 업로드 → 네트워크 탭에서 GA 이벤트 전송 확인

---

### 2. 노션 데이터베이스 설정 ⏱️ 3분

**위치**: https://www.notion.so/ → 좌측 사이드바에서 데이터베이스 찾기

**필수 속성**:
| 속성명 | 타입 | 설명 |
|--------|------|------|
| 이름 | Title | 신청자 이름 |
| 이메일 | Email | 신청자 이메일 |
| 신청일시 | Date | 자동 기록 |

**단계**:
1. 노션에서 데이터베이스 열기 (NOTION_DB_ID 해당)
2. 속성 추가: "이름" (Title), "이메일" (Email), "신청일시" (Date)
3. 공유 → Integration 추가 (NOTION_TOKEN 연결)
4. 테스트: 프리미엄 체험 신청 → 노션에 행 생성 확인

**검증**:
- [ ] 3개 속성 모두 존재
- [ ] Integration 연결됨
- [ ] 테스트 신청 성공

---

### 3. DEBUG 로그 제거 ⏱️ 10분

**파일**: `frontend/app/api/match-actors-batch/route.ts`

**제거할 코드** (lines 9-51):
```typescript
console.log('[DEBUG] Request body:', {
  frontImageBase64: frontImage ? 'present' : 'missing',
  referenceImageBase64: referenceImage ? 'present' : 'missing',
  mode,
  topK
});

console.log('[DEBUG] Sending request to backend:', backendUrl);
// ... 모든 [DEBUG] console.log 제거
```

**파일**: `frontend/app/page.tsx`

**제거할 코드** (lines 134-140):
```typescript
console.log('[DEBUG] Selected file:', file.name, file.size);
console.log('[DEBUG] Base64 length:', base64);
// ... 모든 [DEBUG] console.log 제거
```

**대체 방안** (선택):
```typescript
// 개발 환경에서만 로그
if (process.env.NODE_ENV === 'development') {
  console.log('[DEBUG] Request body:', ...);
}
```

**검증**:
- [ ] 모든 [DEBUG] 로그 제거 또는 개발 환경 조건 추가
- [ ] `npm run build` 성공
- [ ] 배포 후 프로덕션 콘솔에 DEBUG 로그 없음

---

## 🟡 권장 작업 (1주일 내)

### 4. Rate Limiting 구현 ⏱️ 30분

**목적**: API 남용 방지 및 비용 절감

**옵션 A: Vercel Edge Config**
```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const rateLimit = new Map<string, { count: number; reset: number }>()

export function middleware(request: NextRequest) {
  const ip = request.ip || 'anonymous'
  const now = Date.now()
  
  const userLimit = rateLimit.get(ip)
  
  if (userLimit && userLimit.reset > now) {
    if (userLimit.count >= 10) {
      return new NextResponse('Too many requests', { status: 429 })
    }
    userLimit.count++
  } else {
    rateLimit.set(ip, { count: 1, reset: now + 60000 }) // 1분
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: '/api/:path*',
}
```

**옵션 B: Upstash Redis**
```bash
npm install @upstash/ratelimit @upstash/redis
```

```typescript
import { Ratelimit } from "@upstash/ratelimit"
import { Redis } from "@upstash/redis"

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_URL,
  token: process.env.UPSTASH_REDIS_TOKEN,
})

const ratelimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(10, "1 m"),
})

// API route에서 사용
const identifier = request.ip
const { success } = await ratelimit.limit(identifier)
if (!success) return Response.json({ error: 'Too many requests' }, { status: 429 })
```

**검증**:
- [ ] Rate limit 테스트: 연속 11회 요청 → 429 에러
- [ ] 1분 후 다시 가능 확인

---

### 5. 에러 바운더리 추가 ⏱️ 20분

**파일**: `frontend/app/components/ErrorBoundary.tsx`
```typescript
'use client'

import React, { Component, ReactNode } from 'react'
import { logEvent } from '../lib/analytics'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    
    // Analytics 이벤트
    logEvent('error_boundary_triggered', {
      error_message: error.message,
      error_stack: error.stack?.substring(0, 100)
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="mt-4 text-xl font-semibold text-center">문제가 발생했습니다</h2>
            <p className="mt-2 text-sm text-gray-600 text-center">
              일시적인 오류입니다. 페이지를 새로고침해주세요.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition"
            >
              새로고침
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
```

**적용**: `frontend/app/layout.tsx`
```typescript
import { ErrorBoundary } from './components/ErrorBoundary'

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
        <GoogleAnalytics />
        <MicrosoftClarity />
      </body>
    </html>
  )
}
```

---

### 6. 성능 최적화 ⏱️ 40분

**이미지 최적화**: `frontend/app/page.tsx`
```typescript
import Image from 'next/image'

// 기존 <img> 태그 대체
<Image
  src={result.imageUrl}
  alt={result.name}
  width={300}
  height={400}
  loading="lazy"
  quality={75}
  placeholder="blur"
  blurDataURL="data:image/png;base64,iVBORw0KGgo..."
/>
```

**코드 스플리팅**:
```typescript
// 프리미엄 모달을 dynamic import
import dynamic from 'next/dynamic'

const PremiumModal = dynamic(() => import('./components/PremiumModal'), {
  loading: () => <div>로딩 중...</div>,
  ssr: false
})
```

**Lazy Loading**:
```typescript
import { lazy, Suspense } from 'react'

const AnalyticsChart = lazy(() => import('./components/AnalyticsChart'))

<Suspense fallback={<div>차트 로딩 중...</div>}>
  <AnalyticsChart />
</Suspense>
```

---

## 🟢 선택 작업 (2주일 내)

### 7. 테스트 코드 작성 ⏱️ 2시간

**설치**:
```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

**설정**: `jest.config.js`
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
}
```

**테스트 예시**: `frontend/app/__tests__/useSubscription.test.ts`
```typescript
import { renderHook, act } from '@testing-library/react'
import { useSubscription } from '../hooks/useSubscription'

describe('useSubscription', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should initialize with free tier', () => {
    const { result } = renderHook(() => useSubscription())
    
    expect(result.current.userType).toBe('free')
    expect(result.current.imagesRemaining).toBe(10)
    expect(result.current.maxTopK).toBe(5)
  })

  it('should upgrade to premium', () => {
    const { result } = renderHook(() => useSubscription())
    
    act(() => {
      result.current.upgradeToPremium()
    })
    
    expect(result.current.userType).toBe('premium')
    expect(result.current.imagesRemaining).toBe(999999)
    expect(result.current.maxTopK).toBe(50)
  })

  it('should reset monthly quota', () => {
    const { result } = renderHook(() => useSubscription())
    
    // 이미지 사용
    act(() => {
      result.current.decrementImages()
    })
    expect(result.current.imagesRemaining).toBe(9)
    
    // 월 초기화 시뮬레이션
    act(() => {
      result.current.resetMonthlyQuota()
    })
    expect(result.current.imagesRemaining).toBe(10)
  })
})
```

**실행**:
```bash
npm test
npm run test:coverage
```

---

### 8. SEO 최적화 ⏱️ 30분

**메타태그**: `frontend/app/layout.tsx`
```typescript
export const metadata: Metadata = {
  title: 'GenieCasting - AI 배우 매칭 서비스',
  description: '얼굴 분석으로 닮은 배우를 찾아드립니다. 캐스팅 디렉터를 위한 AI 도구',
  keywords: ['배우 매칭', 'AI 캐스팅', '얼굴 분석', '닮은 배우'],
  openGraph: {
    title: 'GenieCasting - AI 배우 매칭',
    description: '얼굴 분석으로 닮은 배우를 찾아드립니다',
    url: 'https://genie-casting.vercel.app',
    siteName: 'GenieCasting',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'ko_KR',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'GenieCasting - AI 배우 매칭',
    description: '얼굴 분석으로 닮은 배우를 찾아드립니다',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
  },
}
```

**Sitemap**: `frontend/app/sitemap.ts`
```typescript
import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: 'https://genie-casting.vercel.app',
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 1,
    },
  ]
}
```

**Robots**: `frontend/app/robots.ts`
```typescript
import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: '/api/',
    },
    sitemap: 'https://genie-casting.vercel.app/sitemap.xml',
  }
}
```

---

### 9. 접근성 개선 ⏱️ 40분

**ARIA 라벨**:
```typescript
<button
  aria-label="프리미엄 플랜 업그레이드"
  role="button"
  onClick={handleUpgrade}
>
  업그레이드
</button>

<input
  type="file"
  aria-label="프로필 이미지 업로드"
  aria-describedby="upload-help"
  accept="image/*"
/>
<span id="upload-help" className="sr-only">
  JPG, PNG 형식 지원, 최대 5MB
</span>
```

**키보드 네비게이션**:
```typescript
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    handleUpgrade()
  }
}

<div
  role="button"
  tabIndex={0}
  onKeyDown={handleKeyDown}
  onClick={handleUpgrade}
>
  업그레이드
</div>
```

**스크린 리더 전용 텍스트**:
```css
/* globals.css */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

---

## 📋 최종 배포 체크리스트

### 환경변수 확인
- [ ] Vercel: `NEXT_PUBLIC_GA_MEASUREMENT_ID` 설정됨
- [ ] Vercel: `NEXT_PUBLIC_CLARITY_PROJECT_ID` 설정됨
- [ ] Vercel: `NOTION_TOKEN` 설정됨
- [ ] Vercel: `NOTION_DB_ID` 설정됨
- [ ] Vercel: `NEXT_PUBLIC_BACKEND_URL` 설정됨
- [ ] Railway: 백엔드 환경변수 모두 설정됨

### 빌드 & 배포
- [ ] `npm run build` 로컬에서 성공
- [ ] TypeScript 에러 0개
- [ ] ESLint 경고 0개
- [ ] Vercel 배포 성공
- [ ] Railway 배포 성공

### 기능 테스트
- [ ] 이미지 업로드 작동
- [ ] 배우 매칭 결과 정상
- [ ] 레퍼런스 모드 작동
- [ ] 프리미엄 CTA 클릭 가능
- [ ] 노션 DB에 신청자 저장됨

### Analytics 검증
- [ ] GA4 이벤트 전송 확인 (DebugView)
- [ ] Clarity 세션 기록 확인
- [ ] 모든 CTA 이벤트 트래킹됨
- [ ] 전환 퍼널 단계별 추적됨

### 성능 & 보안
- [ ] Lighthouse 점수: Performance 90+
- [ ] Lighthouse 점수: Accessibility 90+
- [ ] Lighthouse 점수: SEO 90+
- [ ] Rate limiting 작동 (선택)
- [ ] HTTPS 적용됨
- [ ] CSP 헤더 설정됨 (선택)

### 모니터링
- [ ] GA4 대시보드 설정
- [ ] Clarity 필터 설정
- [ ] 에러 알림 설정 (선택)
- [ ] 주간 리포트 자동화 (선택)

---

## 🚀 배포 후 24시간 내 확인 사항

1. **Analytics 데이터 확인**
   - GA4 실시간 보고서에서 이벤트 수신 확인
   - Clarity에서 첫 세션 녹화 확인

2. **에러 모니터링**
   - Vercel 로그에서 500 에러 없는지 확인
   - Railway 로그에서 API 에러 없는지 확인

3. **사용자 피드백**
   - 노션 DB에 첫 신청자 확인
   - 프리미엄 전환 수 확인

4. **성능 지표**
   - 평균 응답 시간 3초 이내
   - 첫 페이지 로드 2초 이내

---

**다음 단계**: 위 체크리스트 완료 후 → PMF 데이터 수집 → A/B 테스트 시작
