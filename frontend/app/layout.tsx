import './globals.css'
import type { Metadata } from 'next'
import GoogleAnalytics from './components/GoogleAnalytics'
import MicrosoftClarity from './components/MicrosoftClarity'

export const metadata: Metadata = {
  title: '배우 유사도 매칭 - Genie Casting',
  description: '업로드한 이미지로 배우 TOP3 찾기 (Next.js 15.5.7)',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <GoogleAnalytics measurementId={process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID} />
        <MicrosoftClarity projectId={process.env.NEXT_PUBLIC_CLARITY_PROJECT_ID} />
        {children}
      </body>
    </html>
  )
}
