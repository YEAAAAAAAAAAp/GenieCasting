'use client'

import { useEffect, Suspense } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'
import { initGA, logPageView } from '../lib/analytics'

interface GoogleAnalyticsProps {
  measurementId?: string
}

function GoogleAnalyticsInner({ measurementId }: GoogleAnalyticsProps) {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (measurementId) {
      initGA(measurementId)
    }
  }, [measurementId])

  useEffect(() => {
    if (pathname) {
      const url = pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '')
      logPageView(url)
    }
  }, [pathname, searchParams])

  return null
}

export default function GoogleAnalytics({ measurementId }: GoogleAnalyticsProps) {
  return (
    <Suspense fallback={null}>
      <GoogleAnalyticsInner measurementId={measurementId} />
    </Suspense>
  )
}
