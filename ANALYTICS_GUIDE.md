# Google Analytics & Microsoft Clarity 설정 가이드

## 1. Google Analytics 4 설정

### 계정 생성 및 측정 ID 발급
1. https://analytics.google.com/ 접속
2. 관리 (왼쪽 하단 톱니바퀴) → 속성 만들기
3. 속성 이름: "GenieCasting"
4. 데이터 스트림 → 웹 스트림 추가
5. 웹사이트 URL: https://genie-casting.vercel.app
6. 측정 ID 복사 (G-XXXXXXXXXX 형식)

### 환경변수 설정
`.env.local` 파일에 추가:
```env
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

### Vercel 환경변수 설정
1. Vercel Dashboard → Settings → Environment Variables
2. Key: `NEXT_PUBLIC_GA_MEASUREMENT_ID`
3. Value: `G-XXXXXXXXXX`
4. Environment: Production, Preview, Development 모두 체크

## 2. Microsoft Clarity 설정

### 프로젝트 생성 및 ID 발급
1. https://clarity.microsoft.com/ 접속
2. 새 프로젝트 → 프로젝트 이름: "GenieCasting"
3. 웹사이트 URL: https://genie-casting.vercel.app
4. Setup → Get tracking code
5. Project ID 복사 (clarity 코드에서 확인)

### 환경변수 설정
`.env.local` 파일에 추가:
```env
NEXT_PUBLIC_CLARITY_PROJECT_ID=xxxxxxxxxx
```

### Vercel 환경변수 설정
1. Vercel Dashboard → Settings → Environment Variables
2. Key: `NEXT_PUBLIC_CLARITY_PROJECT_ID`
3. Value: `xxxxxxxxxx`
4. Environment: Production만 체크 (개발환경에서는 불필요)

## 3. 추적되는 이벤트 목록

### CTA 클릭 이벤트
- `cta_click/upload_area_premium_link` - 파일 업로드 영역 프리미엄 링크
- `cta_click/topk_slider_upgrade_link` - Top-K 슬라이더 업그레이드 링크
- `cta_click/results_banner_premium_button` - 결과 배너 프리미엄 버튼
- `cta_click/footer_premium_button` - Footer 프리미엄 버튼
- `cta_click/header_badge_upgrade_button` - 헤더 배지 업그레이드 버튼

### 전환 퍼널 이벤트
- `conversion_funnel/premium_modal_opened` - 프리미엄 모달 열림
- `conversion_funnel/premium_modal_upgrade_clicked` - 체험하기 클릭
- `conversion_funnel/premium_modal_closed` - 모달 닫힘
- `conversion_funnel/user_info_modal_opened` - 정보 입력 모달 열림
- `conversion_funnel/user_info_submitted` - 정보 제출 완료
- `conversion_funnel/premium_upgraded` - 프리미엄 업그레이드 완료

### 사용자 행동 이벤트
- `user_action/file_uploaded` - 파일 업로드
- `user_action/analysis_started` - 분석 시작
- `user_action/analysis_completed` - 분석 완료
- `user_action/topk_changed` - Top-K 값 변경

### 제한 도달 이벤트
- `limit_reached/max_images_exceeded` - 최대 이미지 수 초과
- `limit_reached/max_actors_exceeded` - 최대 배우 수 초과
- `limit_reached/monthly_quota_exceeded` - 월 한도 초과

### 성능 측정
- `timing/completion_time` - 분석 완료 시간

### 사용자 속성
- `user_type`: free | premium
- `images_used`: 사용한 이미지 수
- `images_remaining`: 남은 이미지 수

## 4. 대시보드 활용

### Google Analytics 주요 지표
1. **전환율 분석**
   - 탐색 → 맞춤 보고서 → 퍼널 탐색
   - 단계: 페이지 방문 → CTA 클릭 → 모달 열림 → 정보 제출 → 업그레이드

2. **CTA 성과 비교**
   - 탐색 → 맞춤 보고서 → 자유 형식
   - 측정기준: 이벤트 이름
   - 측정항목: 이벤트 수, 전환수
   - 필터: event_category = 'cta_click'

3. **사용자 세그먼트**
   - 탐색 → 세그먼트 만들기
   - 무료 사용자: user_type = 'free'
   - 프리미엄: user_type = 'premium'

### Microsoft Clarity 활용
1. **히트맵 분석**
   - Dashboard → Heatmaps
   - CTA 버튼 클릭 빈도 확인
   - 스크롤 깊이 분석

2. **세션 리플레이**
   - Dashboard → Recordings
   - 필터: 전환 완료 세션
   - 사용자 행동 패턴 파악

3. **좌절 시그널**
   - Dashboard → Rage clicks
   - Dead clicks 확인
   - UI 개선점 도출

## 5. A/B 테스트 제안

### 테스트 항목
1. **가격 변형**
   - A: ₩4,900/월
   - B: ₩9,900/월
   - C: ₩2,900/월 (첫 달 할인)

2. **CTA 문구**
   - A: "프리미엄 체험하기"
   - B: "무료로 시작하기"
   - C: "지금 업그레이드"

3. **무료 플랜 제한**
   - A: 10개 이미지, 5명 배우
   - B: 5개 이미지, 3명 배우
   - C: 20개 이미지, 5명 배우

### 성과 지표 (KPI)
- **CTR (Click Through Rate)**: CTA 클릭률
- **Conversion Rate**: 프리미엄 전환율
- **Drop-off Rate**: 퍼널 이탈률
- **Time to Convert**: 전환까지 소요 시간

## 6. 데이터 분석 주기

### 일일 체크
- 방문자 수
- 신규 프리미엄 가입자
- 에러 발생 여부

### 주간 리뷰
- CTA별 전환율 비교
- 퍼널 단계별 이탈률
- 세션 리플레이 5-10개 시청

### 월간 분석
- PMF 스코어 계산
- 사용자 코호트 분석
- A/B 테스트 결과 평가
