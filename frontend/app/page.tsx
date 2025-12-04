'use client'

import { useMemo, useState, useEffect } from 'react'
import Image from 'next/image'
import { useSubscription } from './hooks/useSubscription'
import PremiumModal from './components/PremiumModal'
import UserInfoModal from './components/UserInfoModal'
import SubscriptionBadge from './components/SubscriptionBadge'
import { PLAN_LIMITS } from './types/subscription'
import { logEvent, setUserProperties, logTiming } from './lib/analytics'

type MatchResult = {
  name: string
  score: number
  image_url?: string | null
  is_reference?: boolean
}

type MatchResponse = {
  results: MatchResult[]
}

type ResultItem = {
  filename: string
  results: MatchResult[]
  imageUrl: string
  referenceScore?: number  // 레퍼런스 모드 점수
  referenceActorName?: string  // 레퍼런스 배우 이름
}

export default function Page() {
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<ResultItem[]>([])
  const [topK, setTopK] = useState<number>(3)
  const [progress, setProgress] = useState<number>(0)
  const [isDragActive, setIsDragActive] = useState(false)
  const [particles, setParticles] = useState<Array<{id: number, x: number, y: number, size: number, delay: number}>>([])
  const [showGuide, setShowGuide] = useState(true)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [totalAnalyzed, setTotalAnalyzed] = useState(0)
  const [targetActor, setTargetActor] = useState<string>('')
  
  // 구독 시스템
  const { subscription, canUseImages, useImages, canUseActors, upgradeToPremium, remainingImages, isPremium } = useSubscription()
  const [showPremiumModal, setShowPremiumModal] = useState(false)
  const [premiumModalReason, setPremiumModalReason] = useState<'images' | 'actors' | 'general'>('general')
  const [showUserInfoModal, setShowUserInfoModal] = useState(false)

  const backendPublic = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  // 사용자 속성 업데이트
  useEffect(() => {
    setUserProperties({
      user_type: isPremium ? 'premium' : 'free',
      images_used: subscription.maxImages - remainingImages,
      images_remaining: remainingImages
    })
  }, [isPremium, remainingImages, subscription.maxImages])

  // Generate floating particles on mount
  useEffect(() => {
    const newParticles = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 4 + 2,
      delay: Math.random() * 5
    }))
    setParticles(newParticles)
  }, [])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setResults([])
    setSuccessMessage(null)
    if (files.length === 0) return
    
    // 구독 제한 확인 - 이미지 수
    if (!canUseImages(files.length)) {
      logEvent({ 
        category: 'limit_reached', 
        action: 'max_images_exceeded', 
        label: `attempted_${files.length}_images` 
      })
      setPremiumModalReason('images')
      setShowPremiumModal(true)
      return
    }
    
    // 구독 제한 확인 - 배우 수
    if (!canUseActors(topK)) {
      logEvent({ 
        category: 'limit_reached', 
        action: 'max_actors_exceeded', 
        label: `attempted_${topK}_actors` 
      })
      setPremiumModalReason('actors')
      setShowPremiumModal(true)
      return
    }
    
    logEvent({ 
      category: 'user_action', 
      action: 'analysis_started', 
      label: `${files.length}_images_${topK}_actors` 
    })
    
    const form = new FormData()
    files.forEach((f: File) => form.append('files', f))
    const qs = new URLSearchParams({ top_k: String(topK) })
    
    // 레퍼런스 배우가 입력된 경우 쿼리에 추가
    if (targetActor.trim()) {
      qs.append('reference_actor', targetActor.trim())
    }
    
    setLoading(true)
    setProgress(0)
    
    const startTime = Date.now()
    
    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90))
    }, 200)
    
    try {
      const resp = await fetch(`/api/match-actors-batch?${qs.toString()}`, { method: 'POST', body: form })
      const data = await resp.json()
      
      if (!resp.ok) {
        const errorMsg = (data as any)?.detail || `요청 실패 (${resp.status})`
        console.error('[ERROR] API Request Failed:', errorMsg)
        throw new Error(errorMsg)
      }
      
      // 백엔드 응답 구조: 
      // 레퍼런스 모드: { items: [{ filename, results: [레퍼런스만], reference_only, reference_score }], ranked_by_reference, reference_actor }
      // 일반 모드: { items: [{ filename, results: [배우 리스트], error? }] }
      
      // 파일명을 키로 하는 이미지 URL 맵 생성
      const fileUrlMap = new Map<string, string>()
      files.forEach((file) => {
        fileUrlMap.set(file.name, URL.createObjectURL(file))
      })
      
      const items: ResultItem[] = (data.items || []).map((it: any) => {
        // 오류가 있는 경우 빈 결과 반환
        if (it.error) {
          console.warn(`[${it.filename}] 처리 실패:`, it.error)
          return {
            filename: it.filename,
            results: [],
            imageUrl: fileUrlMap.get(it.filename) || ''
          }
        }
        
        // 레퍼런스 모드와 일반 모드 처리
        if (targetActor.trim() && it.reference_score !== undefined) {
          // 레퍼런스 모드: 유사도 점수만 표시 (배우 이미지 없음)
          return {
            filename: it.filename,
            results: [],  // 빈 배열 - UI에서 점수만 표시
            imageUrl: fileUrlMap.get(it.filename) || '',
            referenceScore: it.reference_score,
            referenceActorName: it.reference_actor_name
          }
        } else {
          // 일반 모드: 전체 배우 랭킹 리스트 사용
          return {
            filename: it.filename,
            results: (it.results || []) as MatchResult[],
            imageUrl: fileUrlMap.get(it.filename) || ''
          }
        }
      })
      
      setResults(items)
      setProgress(100)
      
      // 분석 완료 시간 측정
      const analysisTime = Date.now() - startTime
      logTiming('analysis', 'completion_time', analysisTime, `${files.length}_images`)
      
      // 성공적으로 처리된 이미지 개수 계산
      const successCount = items.filter(item => item.results.length > 0 || item.referenceScore !== undefined).length
      const errorCount = files.length - successCount
      
      logEvent({ 
        category: 'user_action', 
        action: 'analysis_completed', 
        label: `${successCount}_success_${errorCount}_failed` 
      })
      
      // 이미지 사용 기록
      if (successCount > 0) {
        useImages(successCount)
      }
      
      setTotalAnalyzed(prev => prev + successCount)
      
      if (successCount > 0) {
        setSuccessMessage(`Successfully analyzed ${successCount} image${successCount > 1 ? 's' : ''}!${errorCount > 0 ? ` (${errorCount} failed)` : ''}`)
      } else {
        setError('모든 이미지에서 얼굴을 감지할 수 없습니다. .jpg 또는 .png 파일을 사용하고, 정면 얼굴이 명확한 이미지를 업로드해주세요.')
      }
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (err: any) {
      setError(err?.message || '에러가 발생했습니다')
    } finally {
      clearInterval(progressInterval)
      setLoading(false)
      setTimeout(() => setProgress(0), 1000)
    }
  }

  const onInputChange = (evt: React.ChangeEvent<HTMLInputElement>) => {
    const list = Array.from(evt.target.files || [])
    setFiles(list)
    if (list.length > 0) {
      logEvent({ 
        category: 'user_action', 
        action: 'file_uploaded', 
        label: `${list.length}_files_selected` 
      })
    }
  }

  const onDrop = (evt: React.DragEvent<HTMLDivElement>) => {
    evt.preventDefault()
    setIsDragActive(false)
    const list = Array.from(evt.dataTransfer.files || []) as File[]
    const onlyImages = list.filter((f: File) => f.type.startsWith('image/'))
    setFiles((prev: File[]) => [...prev, ...onlyImages])
    if (onlyImages.length > 0) {
      logEvent({ 
        category: 'user_action', 
        action: 'file_uploaded', 
        label: `${onlyImages.length}_files_dropped` 
      })
    }
  }

  const onDragOver = (evt: React.DragEvent<HTMLDivElement>) => {
    evt.preventDefault()
    setIsDragActive(true)
  }

  const onDragLeave = (evt: React.DragEvent<HTMLDivElement>) => {
    evt.preventDefault()
    setIsDragActive(false)
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearAll = () => {
    setFiles([])
    setResults([])
    setError(null)
    setProgress(0)
  }

  const previews = useMemo(() => files.map((f: File) => ({ name: f.name, url: URL.createObjectURL(f) })), [files])

  return (
    <main className="min-h-screen relative overflow-hidden">
      {/* Genie Magic Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-purple-950 via-indigo-950 to-violet-950">
        {/* Mystical Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-tr from-fuchsia-900/40 via-transparent to-purple-900/40" />
        
        {/* Magical Floating Stars */}
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="absolute rounded-full bg-gradient-to-br from-yellow-200/20 to-pink-400/20 backdrop-blur-sm animate-float"
            style={{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              width: `${particle.size * 2}px`,
              height: `${particle.size * 2}px`,
              animationDelay: `${particle.delay}s`,
              animationDuration: `${15 + Math.random() * 10}s`,
              boxShadow: '0 0 25px rgba(251, 191, 36, 0.3)'
            }}
          />
        ))}
        
        {/* Genie Magical Auras */}
        <div className="absolute top-1/4 right-1/4 w-[700px] h-[700px] bg-fuchsia-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '6s' }} />
        <div className="absolute bottom-1/3 left-1/3 w-[600px] h-[600px] bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }} />
        <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px] bg-amber-400/10 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '10s' }} />
        
        {/* Magical Sparkle Pattern */}
        <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(251, 191, 36, 0.05) 1px, transparent 0)', backgroundSize: '50px 50px' }} />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Magical Genie Navigation Bar */}
        <nav className="backdrop-blur-2xl bg-purple-900/80 border-b border-fuchsia-700/30 shadow-2xl shadow-purple-500/20 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-20">
              {/* Magic Lamp Logo & Brand */}
              <div className="flex items-center gap-4">
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-br from-amber-400 via-fuchsia-500 to-purple-600 rounded-2xl blur-xl opacity-50 group-hover:opacity-100 transition-opacity" />
                  <div className="relative w-12 h-12 rounded-2xl overflow-hidden backdrop-blur-xl border border-amber-300/30 shadow-xl">
                    <Image
                      src="/genie-clean.png"
                      alt="Genie Logo"
                      fill
                      className="object-contain p-1"
                      priority
                    />
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">
                    Genie <span className="bg-gradient-to-r from-amber-300 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent">Match</span>
                  </h1>
                  <p className="text-sm text-purple-300">마법처럼 찾는 닮은 배우 ✨</p>
                </div>
              </div>
              
              {/* Subscription Badge */}
              <SubscriptionBadge
                subscription={subscription}
                remainingImages={remainingImages}
                onUpgradeClick={() => {
                  setPremiumModalReason('general')
                  setShowPremiumModal(true)
                }}
              />
            </div>
          </div>
        </nav>

        {/* Success Toast */}
        {successMessage && (
          <div className="fixed top-24 right-4 z-50 animate-slide-in">
            <div className="backdrop-blur-xl bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-2xl p-4 shadow-2xl shadow-green-500/20 max-w-md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-green-300">{successMessage}</p>
                  <p className="text-xs text-green-400/80">아래에서 결과를 확인하세요</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Guide Banner */}
        {showGuide && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
            <div className="backdrop-blur-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl p-6 shadow-xl relative">
              <button
                onClick={() => setShowGuide(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white mb-2">사용 방법</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-300">
                    <div className="flex items-start gap-2">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold flex-shrink-0">1</span>
                      <span>사람이 포함된 이미지를 업로드하세요</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-xs font-bold flex-shrink-0">2</span>
                      <span>결과 개수를 조정하세요 (1-10)</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-xs font-bold flex-shrink-0">3</span>
                      <span>분석 버튼을 클릭하고 결과를 확인하세요</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Magical Genie Header */}
        <header className="backdrop-blur-2xl bg-purple-900/70 border-b border-fuchsia-700/30 shadow-2xl shadow-purple-500/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              {/* Hero Section with Genie Image */}
              <div className="flex items-center gap-6">
                {/* Animated Genie Image */}
                <div className="relative group hidden md:block">
                  <div className="absolute inset-0 bg-gradient-to-br from-amber-400 via-fuchsia-500 to-purple-600 rounded-full blur-3xl opacity-30 group-hover:opacity-50 transition-opacity duration-500 animate-pulse" />
                  <div className="relative w-40 h-40 transform group-hover:scale-110 transition-all duration-500">
                    <Image
                      src="/genie-clean.png"
                      alt="Genie Magic"
                      fill
                      className="object-contain"
                      priority
                      style={{ 
                        filter: 'drop-shadow(0 10px 30px rgba(251, 191, 36, 0.6)) drop-shadow(0 0 50px rgba(217, 70, 239, 0.4))',
                        imageRendering: 'crisp-edges'
                      }}
                    />
                  </div>
                  {/* Magical sparkle effects */}
                  <div className="absolute top-0 right-0 w-3 h-3 bg-amber-300 rounded-full animate-ping opacity-75" />
                  <div className="absolute top-8 -right-2 w-2 h-2 bg-yellow-200 rounded-full animate-pulse" />
                  <div className="absolute bottom-4 -left-2 w-3 h-3 bg-fuchsia-400 rounded-full animate-bounce opacity-70" style={{ animationDuration: '2s' }} />
                  <div className="absolute -bottom-2 right-8 w-2 h-2 bg-purple-300 rounded-full animate-pulse" style={{ animationDelay: '0.5s' }} />
                </div>
                
                <div className="text-center md:text-left">
                  <h2 className="text-3xl md:text-4xl font-light tracking-tight text-white mb-2">
                    마법처럼 찾는 <span className="font-bold bg-gradient-to-r from-amber-300 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent">닮은꼴 배우</span> ✨
                  </h2>
                  <p className="text-sm text-purple-300">🪔 지니의 마법으로 이미지 속 닮은 배우를 찾아드립니다</p>
                </div>
              </div>

              {/* Magical Database Stats */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3 px-6 py-3 backdrop-blur-xl bg-purple-800/40 border border-fuchsia-700/40 rounded-xl shadow-lg shadow-amber-400/10">
                  <div className="relative">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/30 to-fuchsia-500/30 flex items-center justify-center">
                      <span className="text-xl">⭐</span>
                    </div>
                    <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full animate-pulse border-2 border-purple-900" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold bg-gradient-to-r from-amber-300 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent">
                      100,000+
                    </div>
                    <div className="text-xs text-purple-300 mt-0.5 font-medium">마법의 배우 데이터</div>
                  </div>
                </div>
                {files.length > 0 && (
                  <button
                    onClick={clearAll}
                    className="group px-4 py-3 text-sm text-slate-300 hover:text-white bg-slate-800/50 hover:bg-slate-800 backdrop-blur-xl rounded-xl transition-all duration-300 border border-slate-600/30 hover:border-slate-500/50 shadow-lg hover:shadow-xl hover:shadow-red-500/10"
                  >
                    <svg className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Magical Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="backdrop-blur-xl bg-purple-800/30 border border-fuchsia-700/40 rounded-2xl p-5 hover:border-amber-400/60 transition-all hover:shadow-lg hover:shadow-amber-400/20">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-amber-400/20 flex items-center justify-center">
                  <span className="text-xl">⚡</span>
                </div>
                <h3 className="font-semibold text-white">초고속 마법</h3>
              </div>
              <p className="text-sm text-purple-300">지니의 마법처럼 빠르게 분석합니다</p>
            </div>

            <div className="backdrop-blur-xl bg-purple-800/30 border border-fuchsia-700/40 rounded-2xl p-5 hover:border-fuchsia-400/60 transition-all hover:shadow-lg hover:shadow-fuchsia-400/20">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-fuchsia-500/20 flex items-center justify-center">
                  <span className="text-xl">🔮</span>
                </div>
                <h3 className="font-semibold text-white">안전한 보안</h3>
              </div>
              <p className="text-sm text-purple-300">이미지는 안전하게 처리되며 저장되지 않습니다</p>
            </div>

            <div className="backdrop-blur-xl bg-purple-800/30 border border-fuchsia-700/40 rounded-2xl p-5 hover:border-purple-400/60 transition-all hover:shadow-lg hover:shadow-purple-400/20">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                  <span className="text-xl">✨</span>
                </div>
                <h3 className="font-semibold text-white">높은 정확도</h3>
              </div>
              <p className="text-sm text-purple-300">최첨단 AI 모델로 마법같은 결과를 제공합니다</p>
            </div>
          </div>

          {/* Target Actor Input Section */}
          <div className="backdrop-blur-xl bg-gradient-to-r from-purple-900/60 to-indigo-900/60 border border-amber-400/30 rounded-2xl p-8 mb-8 shadow-xl shadow-amber-400/10">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-400/20 flex items-center justify-center flex-shrink-0">
                <span className="text-2xl">🎯</span>
              </div>
              <div className="flex-1">
                <label htmlFor="targetActor" className="block text-lg font-semibold text-white mb-2">
                  1️⃣ 레퍼런스 배우 입력 ✨
                </label>
                <p className="text-sm text-purple-300 mb-4">
                  시나리오에 떠올린 배우 이름이나 느낌을 입력하세요 (예: 송강호, 전지현, 마동석)
                </p>
                <input
                  id="targetActor"
                  type="text"
                  value={targetActor}
                  onChange={(e) => setTargetActor(e.target.value)}
                  placeholder="레퍼런스 배우 이름을 입력하세요..."
                  className="w-full px-6 py-4 bg-purple-800/40 backdrop-blur-xl border border-fuchsia-600/40 rounded-xl text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400/60 transition-all shadow-inner"
                />
                {targetActor && (
                  <div className="mt-3 flex items-center gap-2 text-sm text-amber-300">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>레퍼런스: <strong>{targetActor}</strong></span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Magical Genie Upload Section */}
          <section className="backdrop-blur-2xl bg-purple-900/50 border border-fuchsia-700/30 rounded-3xl p-12 mb-12 shadow-2xl shadow-purple-500/20">
            <form onSubmit={onSubmit} className="space-y-10">
              {/* Magical Drag & Drop Area */}
              <div
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                className={`
                  relative border-2 border-dashed rounded-3xl p-20 text-center transition-all duration-500
                  ${ isDragActive 
                    ? 'border-amber-400/60 bg-fuchsia-500/10 scale-[1.02] shadow-2xl shadow-amber-400/20' 
                    : 'border-fuchsia-600/40 hover:border-amber-400/60 hover:bg-purple-800/40 hover:shadow-xl hover:shadow-amber-400/10'
                  }
                `}
              >
                <div className="flex flex-col items-center gap-8">
                  <div className="relative group">
                    <div className="absolute inset-0 bg-gradient-to-br from-amber-400 via-fuchsia-500 to-purple-600 rounded-3xl blur-2xl opacity-30 group-hover:opacity-60 transition-opacity duration-500" />
                    <div className="relative w-24 h-24 rounded-3xl bg-gradient-to-br from-amber-400/20 via-fuchsia-500/20 to-purple-600/20 backdrop-blur-xl border border-amber-400/50 flex items-center justify-center shadow-2xl transform group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                      <span className="text-5xl">📸</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-2xl font-light text-white mb-3">
                      {isDragActive ? '✨ 여기에 파일을 놓으세요' : '2️⃣ 지원자 사진 업로드 💫'}
                    </p>
                    <p className="text-sm text-purple-300">
                      오디션 지원 배우들의 프로필 사진을 여러 장 업로드 • JPG, PNG, WEBP
                    </p>
                    {!isPremium && (
                      <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-amber-500/10 to-fuchsia-500/10 border border-amber-400/30 backdrop-blur-sm">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-400 to-yellow-500 flex items-center justify-center flex-shrink-0 shadow-lg">
                            <svg className="w-6 h-6 text-purple-900" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.137 1.619.918 1.88.781.26 1.619-.137 1.88-.918l.818-2.552a1 1 0 00-.285-1.05A3.989 3.989 0 0110 11a3.989 3.989 0 01-2.667-1.019 1 1 0 00-.285-1.05l.818-2.552c.26-.781-.137-1.619-.918-1.88-.781-.26-1.619.137-1.88.918L4.05 7.97z" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="text-sm font-semibold text-white">무료 플랜</h4>
                              <span className="px-2 py-0.5 bg-amber-400/20 text-amber-300 rounded text-xs font-medium">
                                {remainingImages}/{subscription.maxImages}개 남음
                              </span>
                            </div>
                            <p className="text-xs text-purple-300 leading-relaxed mb-2">
                              이번 달 {subscription.maxImages}개 이미지 분석 가능 • 최대 {subscription.maxActors}명 배우 비교
                            </p>
                            <button
                              onClick={() => {
                                logEvent({ 
                                  category: 'cta_click', 
                                  action: 'upload_area_premium_link', 
                                  label: `remaining_images_${remainingImages}` 
                                })
                                setPremiumModalReason('general')
                                setShowPremiumModal(true)
                              }}
                              className="text-xs font-medium text-amber-300 hover:text-amber-200 underline underline-offset-2 transition-colors"
                            >
                              프리미엄으로 무제한 이용하기 →
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  <label className="relative group cursor-pointer">
                    <div className="absolute inset-0 bg-gradient-to-r from-amber-400 via-fuchsia-500 to-purple-600 rounded-xl blur-lg opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="relative px-10 py-4 rounded-xl bg-gradient-to-r from-amber-400 via-fuchsia-500 to-purple-600 text-white font-semibold text-sm transition-all duration-300 group-hover:shadow-2xl group-hover:shadow-amber-400/40 group-hover:scale-105 transform">
                      ✨ 파일 선택
                    </div>
                    <input type="file" accept="image/*" multiple className="hidden" onChange={onInputChange} />
                  </label>
                  {files.length > 0 && (
                    <div className="mt-2 px-6 py-3 rounded-xl bg-gradient-to-r from-slate-800/60 to-slate-700/60 backdrop-blur-xl border border-slate-600/50 shadow-lg">
                      <p className="text-sm font-medium text-slate-200 flex items-center gap-2">
                        <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        {files.length}개 파일 선택됨
                        {!isPremium && files.length > subscription.maxImages && (
                          <span className="ml-2 text-xs text-red-300">
                            (제한 초과: {subscription.maxImages}개까지만 분석 가능)
                          </span>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Magical Wish Counter Slider */}
              <div className="backdrop-blur-xl bg-gradient-to-br from-purple-800/40 to-fuchsia-800/40 border border-amber-400/50 rounded-2xl p-8 shadow-xl shadow-amber-400/10">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/30 to-fuchsia-500/30 backdrop-blur-sm border border-amber-400/50 flex items-center justify-center">
                      <span className="text-xl">🎯</span>
                    </div>
                    <label htmlFor="topk" className="text-base font-medium text-purple-200">
                      3️⃣ 보고 싶은 인원 수 ✨
                    </label>
                    {!isPremium && topK > subscription.maxActors && (
                      <span className="text-xs px-2 py-1 bg-red-500/20 text-red-300 rounded-full border border-red-400/30">
                        제한: {subscription.maxActors}명까지
                      </span>
                    )}
                    {/* Tooltip */}
                    <div className="group relative">
                      <svg className="w-4 h-4 text-purple-400 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div className="hidden group-hover:block absolute left-0 top-6 w-48 p-2 bg-purple-900 border border-fuchsia-700 rounded-lg shadow-xl z-10">
                        <p className="text-xs text-purple-300">
                          {isPremium 
                            ? '프리미엄: 최대 50명까지 가능' 
                            : `무료 플랜: 최대 ${subscription.maxActors}명까지 가능`}
                        </p>
                      </div>
                    </div>
                  </div>
                  <span className="text-3xl font-semibold bg-gradient-to-r from-amber-300 via-fuchsia-400 to-purple-400 bg-clip-text text-transparent px-6 py-2 rounded-xl bg-purple-900/60 border border-amber-400/50 min-w-[70px] text-center shadow-lg">
                    TOP {topK}
                  </span>
                </div>
                <input
                  id="topk"
                  type="range"
                  min={1}
                  max={isPremium ? 50 : subscription.maxActors}
                  value={topK}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTopK(parseInt(e.target.value))}
                  className="w-full h-2 bg-purple-700/50 rounded-full appearance-none cursor-pointer slider-thumb"
                />
                <div className="relative flex justify-between text-xs text-purple-400 mt-4 font-medium px-1">
                  <span className="absolute left-0">1</span>
                  <span className="absolute left-1/2 -translate-x-1/2">{isPremium ? 25 : Math.floor(subscription.maxActors / 2)}</span>
                  <span className="absolute right-0">{isPremium ? 50 : subscription.maxActors}</span>
                </div>
                {!isPremium && (
                  <div className="mt-4 p-3 rounded-lg bg-purple-800/40 border border-purple-600/40">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <svg className="w-4 h-4 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                        </svg>
                        <span className="text-xs text-purple-300">최대 {subscription.maxActors}명까지 비교</span>
                      </div>
                      <button
                        onClick={() => {
                          logEvent({ 
                            category: 'cta_click', 
                            action: 'topk_slider_upgrade_link', 
                            label: `current_topk_${topK}` 
                          })
                          setPremiumModalReason('actors')
                          setShowPremiumModal(true)
                        }}
                        className="text-xs font-medium text-amber-300 hover:text-amber-200 transition-colors"
                      >
                        50명까지 →
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Magical Progress Bar */}
              {(loading || progress > 0) && (
                <div className="space-y-4 backdrop-blur-xl bg-gradient-to-br from-purple-800/40 to-fuchsia-800/40 border border-amber-400/50 rounded-2xl p-6 shadow-xl shadow-amber-400/10">
                  <div className="flex justify-between text-sm text-purple-200">
                    <span className="flex items-center gap-3">
                      {loading && (
                        <svg className="animate-spin h-5 w-5 text-amber-400" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                      )}
                      <span className="font-medium">{loading ? '✨ 마법 분석 중...' : '✨ 완료'}</span>
                    </span>
                    <span className="font-bold bg-gradient-to-r from-amber-300 to-fuchsia-400 bg-clip-text text-transparent">{progress}%</span>
                  </div>
                  <div className="relative w-full bg-purple-900/60 rounded-full h-3 overflow-hidden border border-amber-400/50 shadow-inner">
                    <div
                      className="absolute inset-0 bg-gradient-to-r from-amber-400 via-fuchsia-500 to-purple-600 h-3 rounded-full transition-all duration-500 ease-out shadow-lg shadow-amber-400/50"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                    </div>
                  </div>
                </div>
              )}

              {/* Magical Genie Submit Button */}
              <button
                type="submit"
                disabled={loading || files.length === 0}
                className="relative w-full group overflow-hidden rounded-2xl transition-all duration-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-amber-400 via-fuchsia-500 to-purple-600 blur-xl opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative px-10 py-5 bg-gradient-to-r from-amber-400 via-fuchsia-500 to-purple-600 text-white font-bold text-base transition-all duration-300 group-hover:shadow-2xl group-hover:shadow-amber-400/50 group-hover:scale-[1.02] transform">
                  {loading ? (
                    <span className="flex items-center justify-center gap-3">
                      <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      ✨ 마법 분석 중...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <span className="text-xl">🎬</span>
                      4️⃣ AI 분석 시작 ✨
                    </span>
                  )}
                </div>
              </button>
            </form>

            {/* Premium Error Message */}
            {error && (
              <div className="mt-6 p-5 backdrop-blur-xl bg-gradient-to-r from-red-500/10 to-pink-500/10 border border-red-500/30 rounded-2xl shadow-xl shadow-red-500/10">
                <p className="text-red-300 text-sm flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="font-medium">{error}</span>
                </p>
              </div>
            )}
          </section>

          {/* Luxurious Preview Section */}
          {previews.length > 0 && (
            <section className="mb-12">
              <h2 className="text-2xl font-light text-white mb-8 flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur-sm border border-slate-600/50 flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <span className="text-slate-200">업로드된 이미지</span>
                <span className="ml-auto px-4 py-2 rounded-xl bg-gradient-to-r from-slate-800/60 to-slate-700/60 backdrop-blur-xl border border-slate-600/50 text-sm font-medium text-slate-300">
                  {previews.length}개 이미지
                </span>
              </h2>
              <div className="grid gap-5 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
                {previews.map((p, idx) => (
                  <div key={p.name} className="group relative backdrop-blur-xl bg-slate-800/40 border border-slate-700/40 rounded-2xl overflow-hidden hover:border-slate-600/60 hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-500 hover:scale-105 transform">
                    <div className="relative w-full aspect-square">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={p.url} alt={p.name} className="object-cover w-full h-full" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    </div>
                    <button
                      onClick={() => removeFile(idx)}
                      className="absolute top-3 right-3 bg-slate-900/95 backdrop-blur-xl text-white rounded-xl w-9 h-9 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 hover:bg-red-500 hover:scale-110 border border-slate-700/50 hover:border-red-500 shadow-lg transform"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <div className="p-3 backdrop-blur-xl bg-slate-900/60 border-t border-slate-700/50">
                      <p className="text-xs text-slate-300 truncate font-medium">{p.name}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Premium Results Section */}
          {results.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-light text-white flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur-sm border border-slate-600/50 flex items-center justify-center">
                    <span className="text-xl">🏆</span>
                  </div>
                  <span className="text-slate-200">
                    {targetActor ? (
                      <span>
                        5️⃣ <span className="text-amber-300 font-semibold">&apos;{targetActor}&apos;</span>
                        <span className="text-slate-400 mx-2">닮은 순위</span>
                      </span>
                    ) : (
                      '5️⃣ 분석 결과'
                    )}
                  </span>
                </h2>
                <div className="flex items-center gap-3">
                  <span className="px-4 py-2 rounded-xl bg-gradient-to-r from-green-500/20 to-emerald-500/20 backdrop-blur-xl border border-green-500/30 text-sm font-medium text-green-300">
                    <svg className="w-4 h-4 inline-block mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    {results.length}개 이미지 분석 완료
                  </span>
                  <button
                    onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                    className="px-4 py-2 rounded-xl bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600 text-sm font-medium text-slate-300 hover:text-white transition-all"
                  >
                    맨 위로
                  </button>
                </div>
              </div>
              <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {results.map((res, i) => (
                  <div key={`res-${i}`} className="group backdrop-blur-xl bg-slate-900/50 border border-slate-700/40 rounded-xl overflow-hidden hover:border-slate-600/60 hover:shadow-xl hover:shadow-blue-500/10 transition-all duration-500 hover:scale-[1.02] transform">
                    <div className="bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 border-b border-slate-700/50 p-3 backdrop-blur-xl">
                      <div className="flex items-center gap-3">
                        <span className="w-7 h-7 bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-slate-600/50 rounded-lg flex items-center justify-center text-xs font-bold shadow-lg">
                          {i + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-white text-sm truncate">
                            {res.filename}
                          </h3>
                        </div>
                      </div>
                      {/* 업로드한 이미지 썸네일 - 더 작게 */}
                      {res.imageUrl && (
                        <div className="mt-2 relative w-full aspect-video rounded-lg overflow-hidden border border-slate-600/50">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img 
                            src={res.imageUrl} 
                            alt={res.filename}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      )}
                    </div>
                    <div className="p-3 space-y-3">
                      {/* 레퍼런스 모드: 점수만 표시 (최적화됨) */}
                      {targetActor && res.referenceScore !== undefined ? (
                        <div className="text-center py-6">
                          <div className="mb-4">
                            <div className="w-14 h-14 mx-auto mb-3 rounded-xl bg-gradient-to-br from-amber-500/20 to-fuchsia-500/20 border border-amber-400/50 flex items-center justify-center">
                              <span className="text-3xl">🎯</span>
                            </div>
                            <h4 className="text-base font-bold text-white">
                              <span className="text-amber-300">&apos;{res.referenceActorName}&apos;</span> 유사도
                            </h4>
                          </div>
                          
                          {/* 유사도 점수 표시 - 더 작게 */}
                          <div className="space-y-3">
                            <div className="relative">
                              <div className="w-24 h-24 mx-auto">
                                <svg className="w-full h-full transform -rotate-90">
                                  <circle
                                    cx="48"
                                    cy="48"
                                    r="42"
                                    stroke="currentColor"
                                    strokeWidth="6"
                                    fill="none"
                                    className="text-slate-700/50"
                                  />
                                  <circle
                                    cx="48"
                                    cy="48"
                                    r="42"
                                    stroke="currentColor"
                                    strokeWidth="6"
                                    fill="none"
                                    strokeDasharray={`${2 * Math.PI * 42}`}
                                    strokeDashoffset={`${2 * Math.PI * 42 * (1 - res.referenceScore)}`}
                                    className="text-amber-400 transition-all duration-1000"
                                    strokeLinecap="round"
                                  />
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center">
                                  <div className="text-center">
                                    <div className="text-2xl font-bold bg-gradient-to-r from-amber-300 to-fuchsia-400 bg-clip-text text-transparent">
                                      {(res.referenceScore * 100).toFixed(1)}
                                    </div>
                                    <div className="text-[10px] text-slate-400 -mt-0.5">유사도</div>
                                  </div>
                                </div>
                              </div>
                            </div>
                            
                            <div className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500/10 to-fuchsia-500/10 border border-amber-400/30">
                              <p className="text-xs text-amber-200">
                                {res.referenceScore >= 0.7 ? '🌟 매우 높은 유사도!' :
                                 res.referenceScore >= 0.5 ? '✨ 높은 유사도' :
                                 res.referenceScore >= 0.3 ? '💫 중간 유사도' :
                                 '⭐ 낮은 유사도'}
                              </p>
                            </div>
                          </div>
                        </div>
                      ) : res.results.length === 0 ? (
                        <div className="text-center py-12">
                          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-red-900/30 border border-red-700/50 flex items-center justify-center">
                            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          </div>
                          <p className="text-red-400 text-sm font-semibold mb-2">얼굴 감지 실패</p>
                          <p className="text-slate-400 text-xs leading-relaxed px-4">
                            이미지에서 얼굴을 인식할 수 없습니다.<br />
                            • .jpg 또는 .png 파일을 사용하세요<br />
                            • 정면 얼굴이 명확한 사진을 업로드하세요<br />
                            • .jfif 파일은 지원하지 않습니다
                          </p>
                          <div className="mt-4 text-xs text-slate-500">
                            (개발자 도구 콘솔에서 자세한 오류 확인)
                          </div>
                        </div>
                      ) : (
                        res.results.map((r, rank) => (
                          <div
                            key={`${i}-${r.name}`}
                            className={`relative flex items-center gap-4 p-4 backdrop-blur-xl rounded-xl transition-all duration-300 group/item ${
                              r.is_reference 
                                ? 'bg-gradient-to-br from-amber-500/20 to-fuchsia-500/20 border-2 border-amber-400/60 hover:border-amber-400/80 hover:shadow-2xl hover:shadow-amber-400/30' 
                                : 'bg-gradient-to-br from-slate-800/40 to-slate-700/40 border border-slate-600/50 hover:bg-slate-800/60 hover:border-slate-500/60 hover:shadow-lg hover:shadow-blue-500/10'
                            }`}
                          >
                            {/* Reference Badge */}
                            {r.is_reference && (
                              <div className="absolute -top-2 -right-2 px-3 py-1 bg-gradient-to-r from-amber-400 to-fuchsia-500 rounded-full text-xs font-bold text-white shadow-lg animate-pulse">
                                🎯 레퍼런스
                              </div>
                            )}
                            
                            {/* Rank Badge */}
                            <div className={`flex items-center justify-center w-10 h-10 border rounded-xl text-white text-base font-bold shadow-lg group-hover/item:scale-110 transition-transform duration-300 ${
                              r.is_reference
                                ? 'bg-gradient-to-br from-amber-400/40 to-fuchsia-500/40 border-amber-400/60'
                                : 'bg-gradient-to-br from-blue-500/30 to-purple-500/30 border-slate-600/50'
                            }`}>
                              {rank + 1}
                            </div>
                            
                            {/* Actor Image */}
                            <div className="relative w-20 h-20 shrink-0 bg-slate-800/60 rounded-xl overflow-hidden border border-slate-600/50 shadow-lg group-hover/item:shadow-xl group-hover/item:shadow-blue-500/20 transition-all duration-300">
                              {r.image_url ? (
                                <Image
                                  src={r.image_url}
                                  alt={r.name}
                                  fill
                                  className="object-cover group-hover/item:scale-110 transition-transform duration-500"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center text-slate-500 text-xs font-medium">
                                  N/A
                                </div>
                              )}
                            </div>
                            
                            {/* Actor Info */}
                            <div className="flex-1 min-w-0">
                              <div className="font-semibold text-white text-base truncate mb-2">{r.name}</div>
                              <div className="space-y-2">
                                <div className="flex items-center gap-3">
                                  <div className="flex-1 bg-slate-800/60 rounded-full h-2 overflow-hidden border border-slate-700/50 shadow-inner">
                                    <div
                                      className="h-2 rounded-full bg-gradient-to-r from-blue-500 via-blue-400 to-purple-500 shadow-lg shadow-blue-500/50 transition-all duration-500"
                                      style={{ width: `${r.score * 100}%` }}
                                    >
                                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                                    </div>
                                  </div>
                                  <span className="text-sm font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent whitespace-nowrap w-14 text-right">
                                    {(r.score * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Premium Upgrade Banner - 결과가 있을 때만 표시 */}
          {!isPremium && results.length > 0 && (
            <section className="mt-12 mb-12">
              <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-purple-900 via-fuchsia-900 to-purple-900 border border-amber-400/50 shadow-2xl shadow-amber-400/20">
                {/* Background decorations */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-amber-400/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-fuchsia-500/10 rounded-full blur-3xl" />
                
                <div className="relative px-8 py-12 md:px-12">
                  <div className="max-w-4xl mx-auto">
                    <div className="flex flex-col md:flex-row items-center gap-8">
                      {/* Icon */}
                      <div className="flex-shrink-0">
                        <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-amber-400 to-yellow-500 flex items-center justify-center shadow-2xl animate-bounce-slow">
                          <svg className="w-14 h-14 text-purple-900" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.137 1.619.918 1.88.781.26 1.619-.137 1.88-.918l.818-2.552a1 1 0 00-.285-1.05A3.989 3.989 0 0110 11a3.989 3.989 0 01-2.667-1.019 1 1 0 00-.285-1.05l.818-2.552c.26-.781-.137-1.619-.918-1.88-.781-.26-1.619.137-1.88.918L4.05 7.97z" />
                          </svg>
                        </div>
                      </div>

                      {/* Content */}
                      <div className="flex-1 text-center md:text-left">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-400/20 border border-amber-400/30 mb-3">
                          <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                          <span className="text-xs font-semibold text-amber-300">LIMITED OFFER</span>
                        </div>
                        <h3 className="text-2xl md:text-3xl font-bold text-white mb-2">
                          더 많은 배우를 비교하고 싶으신가요?
                        </h3>
                        <p className="text-purple-200 text-sm md:text-base mb-4">
                          프리미엄으로 무제한 이미지 분석 • 최대 50명 배우 비교 • 우선 처리 지원
                        </p>
                        <div className="flex flex-wrap items-center gap-3 justify-center md:justify-start">
                          <div className="flex items-center gap-2 text-sm text-purple-300">
                            <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            무제한 분석
                          </div>
                          <div className="flex items-center gap-2 text-sm text-purple-300">
                            <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            50명 비교
                          </div>
                          <div className="flex items-center gap-2 text-sm text-purple-300">
                            <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            우선 지원
                          </div>
                        </div>
                      </div>

                      {/* CTA */}
                      <div className="flex-shrink-0">
                        <button
                          onClick={() => {
                            logEvent({ 
                              category: 'cta_click', 
                              action: 'results_banner_premium_button', 
                              label: `after_${results.length}_results` 
                            })
                            setPremiumModalReason('general')
                            setShowPremiumModal(true)
                          }}
                          className="group relative px-8 py-4 rounded-xl bg-gradient-to-r from-amber-400 to-yellow-500 hover:from-amber-500 hover:to-yellow-600 text-purple-900 font-bold text-lg transition-all transform hover:scale-105 shadow-2xl hover:shadow-amber-400/50"
                        >
                          <span className="relative z-10 flex items-center gap-2">
                            프리미엄 체험하기
                            <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                            </svg>
                          </span>
                        </button>
                        <p className="text-center text-xs text-purple-300 mt-2">
                          월 ₩4,900 • 언제든 해지 가능
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}
        </div>

        {/* Magical Genie Footer */}
        <footer className="relative z-10 mt-24 backdrop-blur-2xl bg-purple-900/80 border-t border-fuchsia-700/30 shadow-2xl shadow-purple-500/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-8">
              {/* Brand Section */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="relative w-12 h-12">
                    <Image
                      src="/genie-clean.png"
                      alt="Genie Logo"
                      fill
                      className="object-contain"
                    />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">Genie Match</h3>
                    <p className="text-xs text-purple-300">AI Casting Solution</p>
                  </div>
                </div>
                <p className="text-sm text-purple-300 leading-relaxed mb-4">
                  지니의 마법으로 구동되는 AI 기반 배우 매칭 서비스
                </p>
                <div className="flex items-center gap-2 text-xs text-purple-400">
                  <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                  <span>서비스 정상 운영중</span>
                </div>
              </div>

              {/* Service Links */}
              <div>
                <h4 className="text-white font-semibold mb-4">서비스</h4>
                <ul className="space-y-2.5">
                  <li>
                    <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                      <span className="w-1 h-1 bg-fuchsia-400 rounded-full group-hover:w-2 transition-all" />
                      배우 매칭
                    </a>
                  </li>
                  <li>
                    <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                      <span className="w-1 h-1 bg-fuchsia-400 rounded-full group-hover:w-2 transition-all" />
                      캐스팅 지원
                    </a>
                  </li>
                  <li>
                    <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                      <span className="w-1 h-1 bg-fuchsia-400 rounded-full group-hover:w-2 transition-all" />
                      API 문서
                    </a>
                  </li>
                </ul>
              </div>

              {/* Company & Contact */}
              <div>
                <h4 className="text-white font-semibold mb-4">회사</h4>
                <ul className="space-y-2.5 mb-6">
                  <li>
                    <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                      <span className="w-1 h-1 bg-fuchsia-400 rounded-full group-hover:w-2 transition-all" />
                      소개
                    </a>
                  </li>
                  <li>
                    <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                      <span className="w-1 h-1 bg-fuchsia-400 rounded-full group-hover:w-2 transition-all" />
                      블로그
                    </a>
                  </li>
                  <li>
                    <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                      <span className="w-1 h-1 bg-fuchsia-400 rounded-full group-hover:w-2 transition-all" />
                      채용
                    </a>
                  </li>
                  <li>
                    <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                      <span className="w-1 h-1 bg-fuchsia-400 rounded-full group-hover:w-2 transition-all" />
                      파트너십
                    </a>
                  </li>
                </ul>

                {/* Contact */}
                <div className="pt-4 border-t border-fuchsia-700/20">
                  <h4 className="text-white font-semibold mb-3 text-sm">문의</h4>
                  <a href="mailto:disco922@naver.com" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group mb-3">
                    <svg className="w-4 h-4 text-fuchsia-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    disco922@naver.com
                  </a>
                  <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group mb-3">
                    <svg className="w-4 h-4 text-fuchsia-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    고객 지원
                  </a>
                  <a href="#" className="text-sm text-purple-300 hover:text-white transition-colors flex items-center gap-2 group">
                    <svg className="w-4 h-4 text-fuchsia-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    FAQ
                  </a>
                </div>
              </div>
            </div>

            {/* Social Media */}
            <div className="flex items-center justify-center gap-3 mb-8">
              <a href="#" className="w-9 h-9 rounded-lg bg-purple-800/40 hover:bg-purple-700/60 border border-fuchsia-600/30 hover:border-fuchsia-500/50 flex items-center justify-center text-purple-300 hover:text-white transition-all">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
              </a>
              <a href="#" className="w-9 h-9 rounded-lg bg-purple-800/40 hover:bg-purple-700/60 border border-fuchsia-600/30 hover:border-fuchsia-500/50 flex items-center justify-center text-purple-300 hover:text-white transition-all">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                </svg>
              </a>
              <a href="#" className="w-9 h-9 rounded-lg bg-purple-800/40 hover:bg-purple-700/60 border border-fuchsia-600/30 hover:border-fuchsia-500/50 flex items-center justify-center text-purple-300 hover:text-white transition-all">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
              <a href="#" className="w-9 h-9 rounded-lg bg-purple-800/40 hover:bg-purple-700/60 border border-fuchsia-600/30 hover:border-fuchsia-500/50 flex items-center justify-center text-purple-300 hover:text-white transition-all">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
                </svg>
              </a>
            </div>

            {/* Bottom Bar */}
            <div className="pt-8 border-t border-fuchsia-700/30">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <p className="text-sm text-purple-400">
                  © 2025 Genie Match AI. All rights reserved.
                </p>
                <div className="flex items-center gap-6 text-sm">
                  <a href="#" className="text-purple-400 hover:text-white transition-colors">개인정보처리방침</a>
                  <a href="#" className="text-purple-400 hover:text-white transition-colors">이용약관</a>
                  <a href="#" className="text-purple-400 hover:text-white transition-colors">쿠키 정책</a>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>
      
      {/* Premium Modal */}
      <PremiumModal
        isOpen={showPremiumModal}
        onClose={() => {
          logEvent({ 
            category: 'conversion_funnel', 
            action: 'premium_modal_closed', 
            label: premiumModalReason 
          })
          setShowPremiumModal(false)
        }}
        onUpgrade={() => {
          logEvent({ 
            category: 'conversion_funnel', 
            action: 'premium_modal_upgrade_clicked', 
            label: premiumModalReason 
          })
          setShowPremiumModal(false)
          setShowUserInfoModal(true)
        }}
        reason={premiumModalReason}
      />

      {/* User Info Modal */}
      <UserInfoModal
        isOpen={showUserInfoModal}
        onClose={() => {
          logEvent({ 
            category: 'conversion_funnel', 
            action: 'user_info_modal_closed', 
            label: 'without_submit' 
          })
          setShowUserInfoModal(false)
        }}
        onSubmit={async (name, email) => {
          try {
            logEvent({ 
              category: 'conversion_funnel', 
              action: 'user_info_submitted', 
              label: `name_${name.length}_chars` 
            })
            
            const response = await fetch('/api/premium-signup', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name, email }),
            })

            if (!response.ok) {
              throw new Error('Failed to submit')
            }

            logEvent({ 
              category: 'conversion_funnel', 
              action: 'premium_upgraded', 
              label: 'trial_started' 
            })
            
            // 프리미엄으로 업그레이드
            upgradeToPremium()
            setUserProperties({ 
              user_type: 'premium',
              images_remaining: -1 
            })
            setSuccessMessage('🎉 프리미엄 체험이 시작되었습니다!')
            setTimeout(() => setSuccessMessage(null), 5000)
          } catch (error) {
            console.error('Premium signup error:', error)
            throw error
          }
        }}
      />
    </main>
  )
}
