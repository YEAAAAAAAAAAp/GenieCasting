import ReactGA from 'react-ga4'

// Google Analytics 초기화
export const initGA = (measurementId: string) => {
  if (typeof window !== 'undefined' && measurementId) {
    ReactGA.initialize(measurementId, {
      gaOptions: {
        anonymizeIp: true,
      },
    })
  }
}

// 페이지뷰 트래킹
export const logPageView = (page: string) => {
  if (typeof window !== 'undefined') {
    ReactGA.send({ hitType: 'pageview', page })
  }
}

// 이벤트 타입 정의
export type AnalyticsEvent = 
  // CTA 클릭 이벤트
  | { category: 'cta_click', action: 'upload_area_premium_link', label: string }
  | { category: 'cta_click', action: 'topk_slider_upgrade_link', label: string }
  | { category: 'cta_click', action: 'results_banner_premium_button', label: string }
  | { category: 'cta_click', action: 'footer_premium_button', label: string }
  | { category: 'cta_click', action: 'header_badge_upgrade_button', label: string }
  
  // 전환 퍼널 이벤트
  | { category: 'conversion_funnel', action: 'premium_modal_opened', label: string }
  | { category: 'conversion_funnel', action: 'premium_modal_closed', label: string }
  | { category: 'conversion_funnel', action: 'premium_modal_upgrade_clicked', label: string }
  | { category: 'conversion_funnel', action: 'user_info_modal_opened', label: string }
  | { category: 'conversion_funnel', action: 'user_info_modal_closed', label: string }
  | { category: 'conversion_funnel', action: 'user_info_submitted', label: string }
  | { category: 'conversion_funnel', action: 'premium_upgraded', label: string }
  
  // 사용자 행동 이벤트
  | { category: 'user_action', action: 'file_uploaded', label: string }
  | { category: 'user_action', action: 'analysis_started', label: string }
  | { category: 'user_action', action: 'analysis_completed', label: string }
  | { category: 'user_action', action: 'topk_changed', label: string }
  
  // 제한 이벤트
  | { category: 'limit_reached', action: 'max_images_exceeded', label: string }
  | { category: 'limit_reached', action: 'max_actors_exceeded', label: string }
  | { category: 'limit_reached', action: 'monthly_quota_exceeded', label: string }

// 이벤트 로깅
export const logEvent = (event: AnalyticsEvent) => {
  if (typeof window !== 'undefined') {
    ReactGA.event({
      category: event.category,
      action: event.action,
      label: event.label,
    })
    
    // 콘솔에도 로깅 (개발 중)
    if (process.env.NODE_ENV === 'development') {
      console.log('📊 Analytics Event:', event)
    }
  }
}

// 커스텀 이벤트 (전환 추적용)
export const logConversion = (conversionType: 'premium_trial' | 'premium_purchase', value?: number) => {
  if (typeof window !== 'undefined') {
    ReactGA.event({
      category: 'conversion',
      action: conversionType,
      value: value || 0,
    })
  }
}

// 사용자 속성 설정
export const setUserProperties = (properties: {
  user_type?: 'free' | 'premium'
  images_used?: number
  images_remaining?: number
}) => {
  if (typeof window !== 'undefined') {
    ReactGA.set(properties)
  }
}

// 타이밍 이벤트 (성능 측정)
export const logTiming = (category: string, variable: string, value: number, label?: string) => {
  if (typeof window !== 'undefined') {
    ReactGA.event({
      category: 'timing',
      action: variable,
      value: value,
      label: label || category,
    })
  }
}
