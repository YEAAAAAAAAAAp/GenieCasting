import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: '배우 유사도 매칭',
  description: '업로드한 이미지로 배우 TOP3 찾기',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
