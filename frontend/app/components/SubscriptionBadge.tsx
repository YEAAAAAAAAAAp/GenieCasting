import { SubscriptionState, PLAN_LIMITS } from '../types/subscription'

interface SubscriptionBadgeProps {
  subscription: SubscriptionState
  remainingImages: number
  onUpgradeClick: () => void
}

export default function SubscriptionBadge({ subscription, remainingImages, onUpgradeClick }: SubscriptionBadgeProps) {
  const isPremium = subscription.plan === 'premium'

  return (
    <div className="flex items-center gap-3">
      {/* Plan badge */}
      <div className={`px-4 py-2 rounded-full font-semibold text-sm shadow-lg ${
        isPremium 
          ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-purple-900' 
          : 'bg-white/10 text-white border border-white/20'
      }`}>
        {isPremium ? (
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.137 1.619.918 1.88.781.26 1.619-.137 1.88-.918l.818-2.552a1 1 0 00-.285-1.05A3.989 3.989 0 0110 11a3.989 3.989 0 01-2.667-1.019 1 1 0 00-.285-1.05l.818-2.552c.26-.781-.137-1.619-.918-1.88-.781-.26-1.619.137-1.88.918L4.05 7.97z" />
            </svg>
            <span>프리미엄</span>
          </div>
        ) : (
          <span>무료 플랜</span>
        )}
      </div>

      {/* Usage info */}
      {!isPremium && (
        <div className="bg-white/5 px-3 py-2 rounded-lg text-sm">
          <span className="text-white/70">남은 이미지: </span>
          <span className={`font-bold ${remainingImages <= 2 ? 'text-red-400' : 'text-white'}`}>
            {remainingImages}/{subscription.maxImages}
          </span>
        </div>
      )}

      {isPremium && (
        <div className="bg-white/5 px-3 py-2 rounded-lg text-sm text-white/70">
          무제한 이용 중 ✨
        </div>
      )}

      {/* Upgrade button (for free users) */}
      {!isPremium && (
        <button
          onClick={onUpgradeClick}
          className="px-4 py-2 bg-gradient-to-r from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600 text-purple-900 font-semibold text-sm rounded-full transition-all transform hover:scale-105 shadow-lg"
        >
          업그레이드
        </button>
      )}
    </div>
  )
}
