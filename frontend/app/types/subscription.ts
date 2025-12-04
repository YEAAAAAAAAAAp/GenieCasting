// 구독 플랜 타입
export type SubscriptionPlan = 'free' | 'premium'

// 구독 상태
export interface SubscriptionState {
  plan: SubscriptionPlan
  maxActors: number        // 보고 싶은 배우 수 제한
  maxImages: number        // 업로드 가능한 이미지 수 제한
  usedImages: number       // 이번 달 사용한 이미지 수
  resetDate: string        // 다음 리셋 날짜 (무료 플랜만)
}

// 플랜별 제한
export const PLAN_LIMITS = {
  free: {
    maxActors: 5,
    maxImages: 10,
    price: 0,
    label: '무료 플랜',
    features: [
      '월 10개 이미지 분석',
      '배우 5명까지 비교',
      '기본 정확도'
    ]
  },
  premium: {
    maxActors: 50,
    maxImages: -1, // 무제한
    price: 4900,
    label: '프리미엄 플랜',
    features: [
      '무제한 이미지 분석',
      '배우 50명까지 비교',
      '고해상도 정확도',
      '우선 처리'
    ]
  }
} as const

// 로컬스토리지 키
export const STORAGE_KEY = 'genie_subscription'
