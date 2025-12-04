# PMF 측정 완료 체크리스트

## ✅ 완료된 작업

### 1. 프리미엄 구독 시스템
- [x] 무료 플랜 (10개 이미지/월, 5명 배우)
- [x] 프리미엄 플랜 (무제한 이미지, 50명 배우, ₩4,900/월)
- [x] LocalStorage 기반 구독 추적
- [x] 월별 사용량 자동 리셋

### 2. 전략적 CTA 배치 (4개 전환 지점)
- [x] **파일 업로드 영역** - 무료 플랜 한도 안내 + 프리미엄 티저
- [x] **Top-K 슬라이더** - 잠금 UI + 업그레이드 링크
- [x] **결과 배너** - 대형 프리미엄 업그레이드 배너
- [x] **Footer** - 프리미엄 플랜 전용 카드

### 3. 전환 퍼널
- [x] CTA 클릭 → 프리미엄 모달
- [x] "프리미엄 체험하기" → 사용자 정보 입력 모달
- [x] 이름/이메일 입력 → 노션 데이터베이스 저장
- [x] 저장 완료 → 프리미엄 자동 업그레이드

### 4. 데이터 수집
- [x] **노션 통합**: 체험 신청자 정보 자동 저장
  - 노션 DB 연동 완료 (환경변수로 관리)
  
- [x] **Google Analytics 4**: 이벤트 트래킹
  - 4개 CTA 클릭 추적
  - 7단계 전환 퍼널 분석
  - 사용자 행동 패턴 수집
  - 제한 도달 이벤트 (friction points)
  - 성능 측정 (분석 완료 시간)

- [x] **Microsoft Clarity**: 히트맵 & 세션 리플레이
  - CTA 클릭 히트맵
  - 스크롤 깊이 분석
  - 세션 리플레이
  - Rage/Dead 클릭 감지

## 📊 추적 중인 이벤트

### CTA 클릭 (5개)
1. `cta_click/upload_area_premium_link` - 업로드 영역
2. `cta_click/topk_slider_upgrade_link` - 슬라이더
3. `cta_click/results_banner_premium_button` - 결과 배너
4. `cta_click/footer_premium_button` - Footer
5. `cta_click/header_badge_upgrade_button` - 헤더 배지

### 전환 퍼널 (7단계)
1. `conversion_funnel/premium_modal_opened`
2. `conversion_funnel/premium_modal_upgrade_clicked`
3. `conversion_funnel/premium_modal_closed`
4. `conversion_funnel/user_info_modal_opened`
5. `conversion_funnel/user_info_submitted`
6. `conversion_funnel/user_info_modal_closed`
7. `conversion_funnel/premium_upgraded`

### 사용자 행동 (4개)
1. `user_action/file_uploaded`
2. `user_action/analysis_started`
3. `user_action/analysis_completed`
4. `user_action/topk_changed`

### 제한 도달 (3개)
1. `limit_reached/max_images_exceeded`
2. `limit_reached/max_actors_exceeded`
3. `limit_reached/monthly_quota_exceeded`

## 🚀 다음 단계

### 환경변수 설정 필요

**Vercel Dashboard → Settings → Environment Variables에 추가:**

```env
# 노션 통합
NOTION_TOKEN=your_notion_integration_token
NOTION_DB_ID=your_database_id

# Google Analytics (필수)
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Microsoft Clarity (권장)
NEXT_PUBLIC_CLARITY_PROJECT_ID=xxxxxxxxxx
```

### Google Analytics 4 설정
1. https://analytics.google.com/ 접속
2. 관리 → 속성 만들기 → "GenieCasting"
3. 데이터 스트림 → 웹 추가 → https://genie-casting.vercel.app
4. 측정 ID (G-XXXXXXXXXX) 복사
5. Vercel에 환경변수 추가

### Microsoft Clarity 설정
1. https://clarity.microsoft.com/ 접속
2. 새 프로젝트 → "GenieCasting"
3. 웹사이트 URL: https://genie-casting.vercel.app
4. Setup → Project ID 복사
5. Vercel에 환경변수 추가 (Production만)

## 📈 PMF 측정 지표

### 핵심 KPI
1. **전환율 (Conversion Rate)**
   - 방문자 → 프리미엄 체험 신청
   - 목표: 5-10%

2. **퍼널 이탈률 (Drop-off Rate)**
   - 각 단계별 이탈률 추적
   - 개선 우선순위 파악

3. **CTA 효율성**
   - 어느 CTA가 가장 효과적인지
   - 배치 최적화

4. **사용자 세그먼트**
   - 무료 → 프리미엄 전환 패턴
   - 재방문율

### 분석 대시보드
- **GA4 퍼널 분석**: 전환 경로 시각화
- **Clarity 히트맵**: CTA 클릭 분포
- **세션 리플레이**: 실제 사용자 행동 관찰
- **노션 DB**: 체험 신청자 명단

## 🎯 A/B 테스트 제안

### 1차 테스트 (가격)
- A: ₩4,900/월
- B: ₩9,900/월  
- C: ₩2,900/월 (첫 달 50% 할인)

### 2차 테스트 (CTA 문구)
- A: "프리미엄 체험하기"
- B: "무료로 시작하기"
- C: "지금 업그레이드"

### 3차 테스트 (무료 플랜 한도)
- A: 10개/5명 (현재)
- B: 5개/3명 (더 엄격)
- C: 20개/5명 (더 관대)

## 📚 문서

- **설정 가이드**: `ANALYTICS_GUIDE.md`
- **이벤트 목록**: 위 섹션 참조
- **대시보드 활용**: ANALYTICS_GUIDE.md 참조

## ✨ 배포 상태

- ✅ Railway (백엔드): https://geniecasting-production.up.railway.app
- ✅ Vercel (프론트엔드): https://genie-casting.vercel.app
- ✅ 노션 DB: 연동 완료
- ⏳ Google Analytics: 환경변수 설정 대기
- ⏳ Microsoft Clarity: 환경변수 설정 대기

---

**마지막 업데이트**: 2025-12-05
**현재 단계**: Analytics 통합 완료, 환경변수 설정 대기
