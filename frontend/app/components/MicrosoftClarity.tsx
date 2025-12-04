'use client'

import { useEffect } from 'react'

interface MicrosoftClarityProps {
  projectId?: string
}

export default function MicrosoftClarity({ projectId }: MicrosoftClarityProps) {
  useEffect(() => {
    if (!projectId || typeof window === 'undefined') return

    // Microsoft Clarity 스크립트 삽입
    ;(function(c: any, l: any, a: string, r: string, i: string, t?: any, y?: any) {
      c[a] = c[a] || function() { (c[a].q = c[a].q || []).push(arguments) }
      t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y)
    })(window, document, "clarity", "script", projectId)

    if (process.env.NODE_ENV === 'development') {
      console.log('📹 Microsoft Clarity initialized:', projectId)
    }
  }, [projectId])

  return null
}
