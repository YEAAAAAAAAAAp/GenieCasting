import { PLAN_LIMITS } from '../types/subscription'

interface PremiumModalProps {
  isOpen: boolean
  onClose: () => void
  onUpgrade: () => void
  reason?: 'images' | 'actors' | 'general'
}

export default function PremiumModal({ isOpen, onClose, onUpgrade, reason = 'general' }: PremiumModalProps) {
  if (!isOpen) return null

  const getMessage = () => {
    switch (reason) {
      case 'images':
        return '이번 달 무료 이미지 분석 한도를 모두 사용하셨습니다.'
      case 'actors':
        return `무료 플랜은 최대 ${PLAN_LIMITS.free.maxActors}명의 배우만 비교할 수 있습니다.`
      default:
        return '더 많은 기능을 이용하려면 프리미엄으로 업그레이드하세요.'
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 rounded-2xl shadow-2xl overflow-hidden animate-scale-in">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Content */}
        <div className="p-8">
          {/* Crown icon */}
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-yellow-400 rounded-full flex items-center justify-center animate-bounce-slow">
              <svg className="w-10 h-10 text-purple-900" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.137 1.619.918 1.88.781.26 1.619-.137 1.88-.918l.818-2.552a1 1 0 00-.285-1.05A3.989 3.989 0 0110 11a3.989 3.989 0 01-2.667-1.019 1 1 0 00-.285-1.05l.818-2.552c.26-.781-.137-1.619-.918-1.88-.781-.26-1.619.137-1.88.918L4.05 7.97z" />
              </svg>
            </div>
          </div>

          {/* Title */}
          <h2 className="text-3xl font-bold text-center text-white mb-3">
            프리미엄으로 업그레이드
          </h2>

          {/* Reason */}
          <p className="text-center text-purple-200 mb-6">
            {getMessage()}
          </p>

          {/* Free vs Premium comparison */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            {/* Free */}
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-sm font-semibold text-purple-300 mb-2">무료 플랜</div>
              <div className="space-y-2 text-sm text-white/80">
                <div>• 월 {PLAN_LIMITS.free.maxImages}개 이미지</div>
                <div>• {PLAN_LIMITS.free.maxActors}명 비교</div>
                <div className="text-purple-300">₩0</div>
              </div>
            </div>

            {/* Premium */}
            <div className="bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-lg p-4 shadow-lg">
              <div className="text-sm font-semibold text-purple-900 mb-2">프리미엄</div>
              <div className="space-y-2 text-sm text-purple-900 font-medium">
                <div>• 무제한 이미지 ✨</div>
                <div>• {PLAN_LIMITS.premium.maxActors}명 비교</div>
                <div className="text-purple-900 font-bold">₩{PLAN_LIMITS.premium.price.toLocaleString()}/월</div>
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="bg-white/5 rounded-lg p-4 mb-6">
            <div className="text-sm font-semibold text-white mb-3">프리미엄 혜택</div>
            <div className="space-y-2">
              {PLAN_LIMITS.premium.features.map((feature, idx) => (
                <div key={idx} className="flex items-center text-sm text-purple-200">
                  <svg className="w-4 h-4 mr-2 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {feature}
                </div>
              ))}
            </div>
          </div>

          {/* CTA buttons */}
          <div className="space-y-3">
            <button
              onClick={onUpgrade}
              className="w-full bg-gradient-to-r from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600 text-purple-900 font-bold py-3 px-6 rounded-lg transition-all transform hover:scale-105 shadow-lg"
            >
              프리미엄 체험하기 - ₩{PLAN_LIMITS.premium.price.toLocaleString()}/월
            </button>
            <button
              onClick={onClose}
              className="w-full bg-white/10 hover:bg-white/20 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              나중에 하기
            </button>
          </div>

          {/* Note */}
          <p className="text-xs text-center text-purple-300 mt-4">
            * 데모 버전입니다. 실제 결제는 진행되지 않습니다.
          </p>
        </div>
      </div>
    </div>
  )
}
