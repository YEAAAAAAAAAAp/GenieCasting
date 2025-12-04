import { useState, useEffect } from 'react'
import { SubscriptionState, SubscriptionPlan, PLAN_LIMITS, STORAGE_KEY } from '../types/subscription'

// 다음 달 1일 계산
function getNextMonthFirstDay(): string {
  const now = new Date()
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1)
  return nextMonth.toISOString()
}

// 초기 구독 상태
function getInitialSubscription(): SubscriptionState {
  if (typeof window === 'undefined') {
    return {
      plan: 'free',
      maxActors: PLAN_LIMITS.free.maxActors,
      maxImages: PLAN_LIMITS.free.maxImages,
      usedImages: 0,
      resetDate: getNextMonthFirstDay()
    }
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const data = JSON.parse(stored) as SubscriptionState
      
      // 리셋 날짜가 지났는지 확인 (무료 플랜만)
      if (data.plan === 'free' && new Date(data.resetDate) < new Date()) {
        return {
          ...data,
          usedImages: 0,
          resetDate: getNextMonthFirstDay()
        }
      }
      
      return data
    }
  } catch (error) {
    console.error('Failed to load subscription:', error)
  }

  return {
    plan: 'free',
    maxActors: PLAN_LIMITS.free.maxActors,
    maxImages: PLAN_LIMITS.free.maxImages,
    usedImages: 0,
    resetDate: getNextMonthFirstDay()
  }
}

export function useSubscription() {
  const [subscription, setSubscription] = useState<SubscriptionState>(getInitialSubscription)

  // 로컬스토리지 저장
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(subscription))
    }
  }, [subscription])

  // 이미지 사용 가능 여부 확인
  const canUseImages = (count: number): boolean => {
    if (subscription.plan === 'premium') {
      return true // 프리미엄은 무제한
    }
    return subscription.usedImages + count <= subscription.maxImages
  }

  // 이미지 사용 기록
  const useImages = (count: number) => {
    if (subscription.plan === 'premium') {
      return // 프리미엄은 카운트 안 함
    }
    setSubscription(prev => ({
      ...prev,
      usedImages: Math.min(prev.usedImages + count, prev.maxImages)
    }))
  }

  // 배우 수 제한 확인
  const canUseActors = (count: number): boolean => {
    return count <= subscription.maxActors
  }

  // 프리미엄 업그레이드
  const upgradeToPremium = () => {
    setSubscription({
      plan: 'premium',
      maxActors: PLAN_LIMITS.premium.maxActors,
      maxImages: PLAN_LIMITS.premium.maxImages,
      usedImages: 0,
      resetDate: '' // 프리미엄은 리셋 없음
    })
  }

  // 무료 플랜으로 다운그레이드 (테스트용)
  const downgradeToFree = () => {
    setSubscription({
      plan: 'free',
      maxActors: PLAN_LIMITS.free.maxActors,
      maxImages: PLAN_LIMITS.free.maxImages,
      usedImages: 0,
      resetDate: getNextMonthFirstDay()
    })
  }

  // 남은 이미지 수
  const remainingImages = subscription.plan === 'premium' 
    ? -1 // 무제한
    : subscription.maxImages - subscription.usedImages

  return {
    subscription,
    canUseImages,
    useImages,
    canUseActors,
    upgradeToPremium,
    downgradeToFree,
    remainingImages,
    isPremium: subscription.plan === 'premium'
  }
}
