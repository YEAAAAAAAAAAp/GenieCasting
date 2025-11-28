# Genie Match - AI 캐스팅 솔루션 🪔✨

감독이 시나리오에 생각한 **유명 배우 이름을 입력**하고, 지원받은 배우들의 사진을 업로드하면 **얼굴 유사도 기준으로 지원자를 자동 랭킹**해주는 AI 기반 캐스팅 매칭 서비스입니다.

**🌐 라이브 데모**: https://genie-casting.vercel.app  
**📊 백엔드 API**: https://geniecasting-production.up.railway.app

## 주요 특징

- 🎯 **레퍼런스 배우 매칭**: 302명의 한국 배우 데이터베이스 내장
- 🔮 **AI 얼굴 인식**: InsightFace AuraFace-v1 모델 기반 (512차원 임베딩)
- ⚡ **배치 처리**: 여러 지원자 이미지 동시 분석 및 실시간 진행률 표시
- ✨ **Genie 테마**: Purple/Fuchsia/Amber 그라데이션의 마법적인 사용자 경험
- 📊 **Top-K 조절**: 1~10개의 유사 배우 결과 개수 조절
- 🎨 **직관적 UI**: 드래그&드롭 업로드, 반응형 디자인, 애니메이션 효과

## 기술 스택

### 백엔드
- **FastAPI 0.115.5**: REST API 서버
- **InsightFace (AuraFace-v1)**: 얼굴 인식 임베딩 모델 (512차원 벡터)
- **ONNX Runtime**: 모델 추론 최적화 엔진
- **OpenCV 4.10**: 이미지 전처리 및 변환
- **NumPy 1.26**: 벡터 연산 (InsightFace 호환성 위해 <2.0 버전)
- **Uvicorn**: ASGI 웹 서버

### 프론트엔드
- **Next.js 14.2.10**: App Router 기반 서버 사이드 렌더링
- **TypeScript**: 정적 타입 검사
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Genie Theme**: 커스텀 Purple/Fuchsia/Amber 색상 팔레트

### 인프라
- **Railway**: 백엔드 호스팅 (Railpack 빌더)
- **Vercel**: 프론트엔드 호스팅 (CDN, Edge Functions)
- **GitHub**: 버전 관리 및 CI/CD 트리거

## 배포 아키텍처

```
[사용자 브라우저]
       ↓
[Vercel - Next.js Frontend]
   (genie-casting.vercel.app)
       ↓ API Proxy
[Railway - FastAPI Backend]
   (geniecasting-production.up.railway.app)
       ↓
[InsightFace AuraFace-v1 모델]
       ↓
[배우 인덱스 (302명 × 512차원)]
```

**배포 완료 상태**:
- ✅ Railway 백엔드: 정상 작동 (배우 인덱스 302명 로드 완료)
- ✅ Vercel 프론트엔드: 정상 배포 (환경변수 설정 완료)
- ✅ CORS 설정: 모든 origin 허용
- ✅ CI/CD: GitHub push 시 자동 배포

## 프로젝트 구조

```
backend/
  app/
    main.py                      # FastAPI 엔드포인트
    models/schemas.py            # Pydantic 스키마
    services/
      embeddings.py              # InsightFace 얼굴 임베딩 생성
      face_preprocess.py         # 얼굴 전처리 (옵션)
      search.py                  # 배우 인덱스 검색
    data/                        # 생성된 인덱스 파일
      embeddings.npy             # 배우 임베딩 벡터
      metadata.json              # 배우 메타데이터
      actors/                    # 배우 대표 이미지
  scripts/
    build_actor_index_insightface.py  # InsightFace 인덱스 빌더

frontend/
  app/
    page.tsx                     # 메인 페이지 (Genie UI)
    layout.tsx                   # 레이아웃
    globals.css                  # Tailwind 설정
    api/
      match-actors/route.ts      # 단일 매칭 API 라우트
      match-actors-batch/route.ts # 배치 매칭 API 라우트
  public/
    genie-clean.png              # 지니 로고 (투명 배경, 소문자)
    Genie.png                    # 지니 이미지 (원본)
  next.config.mjs                # Next.js 설정
  tailwind.config.js             # Tailwind 커스텀 테마 (Genie 색상)

dataset/                         # 배우 데이터셋 (302명)
  강나언/
    001.jpg, 002.jpg, ...
  고윤정/
    001.jpg, 002.jpg, ...
  (... 300명 더)

requirements.txt                 # Python 의존성
nixpacks.toml                    # Railway 빌드 설정
runtime.txt                      # Python 버전 (3.12.10)
.gitignore                       # Git 제외 파일 (환경변수, 캐시 등)
README.md                        # 프로젝트 문서
```

## 설치 및 실행

### 1. Python 환경 설정 (Windows PowerShell)

**요구사항**: Python 3.10 이상

```powershell
# 가상환경 생성 및 활성화
python -m venv .venv
.\.venv\Scripts\Activate

# Python 패키지 설치
pip install -r requirements.txt
```

> **참고**: InsightFace는 자동으로 AuraFace-v1 모델(~100MB)을 다운로드합니다. Windows에서는 Visual C++ Build Tools가 필요할 수 있습니다.

**주요 의존성**:
- `numpy>=1.21.0,<2.0.0` (InsightFace 호환성)
- `opencv-python==4.10.0.84` (numpy<2 호환)
- `insightface>=0.7.3` (AuraFace-v1 모델)

### 2. 배우 인덱스 생성

**중요**: 프로덕션 환경(Railway)에서는 배포 시 자동으로 인덱스가 생성됩니다(`nixpacks.toml` 설정). 로컬 개발 환경에서만 수동 실행이 필요합니다.

배우 이미지 데이터셋을 준비합니다. 폴더 구조 방식을 권장합니다.

#### 폴더 구조 (권장)

```
C:\data\actors\
  송강호\
    image1.jpg
    image2.jpg
  전지현\
    photo1.png
    photo2.png
  이정재\
    pic1.jpg
```

```powershell
# PYTHONPATH 설정하여 인덱스 빌드
$env:PYTHONPATH="C:\Users\disco\Desktop\25-2\서비스디자인\GenieCasting"
python backend\scripts\build_actor_index_insightface.py --dataset dataset\ --clusters 1
```

#### CSV 방식 (옵션)

```csv
name,image_path
송강호,C:\data\images\song1.jpg
송강호,C:\data\images\song2.jpg
전지현,C:\data\images\jeon1.png
```

```powershell
python backend\scripts\build_actor_index_insightface.py --csv C:\data\actors.csv --clusters 1
```

**생성 결과**: `backend/app/data/` 폴더에 다음 파일이 생성됩니다.
- `embeddings.npy`: 배우 임베딩 벡터 (302 × 512 차원, float32)
- `metadata.json`: 배우 이름, 대표 이미지 경로 메타데이터
- `actors/`: 배우별 대표 이미지 복사본 (API에서 `/actors/<배우명>/<이미지>` 형태로 제공)

**처리 과정**:
- 각 배우별로 10장의 이미지에서 얼굴 검출
- 검출된 얼굴을 512차원 벡터로 임베딩
- 배우별 평균 벡터 계산 (대표 얼굴)
- 일부 이미지는 얼굴 감지 실패 가능 (손상된 파일 등) - 정상 동작

### 3. 서버 실행

#### 백엔드 서버 (FastAPI)

```powershell
# 가상환경 활성화 (필수)
.\.venv\Scripts\Activate.ps1

# 백엔드 서버 시작
$env:PYTHONPATH=(Get-Location).Path
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

서버 실행 후: 
- API 문서: http://localhost:8000/docs 
- 인덱스 상태: http://localhost:8000/index-status (actor_count: 302 확인)

#### 프론트엔드 서버 (Next.js)

새 터미널을 열고:

```powershell
cd frontend

# 환경 변수 설정 (.env.local 파일 생성)
@"
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
"@ | Out-File -FilePath .env.local -Encoding utf8

# 패키지 설치 (최초 1회)
npm install

# 개발 서버 시작
npm run dev
```

브라우저에서 http://localhost:3000 접속

**주의사항**:
- `.env.local` 파일은 Git에 커밋되지 않습니다 (`.gitignore` 설정됨)
- 프로덕션 환경변수는 Vercel 대시보드에서 별도 설정

## 사용 방법

### 기본 워크플로우
1. **레퍼런스 배우 입력**: 캐스팅하고 싶은 유명 배우 이름 입력 (예: 송강호, 전지현)
2. **지원자 사진 업로드**: 지원자들의 사진을 드래그&드롭 또는 파일 선택
3. **결과 개수 조절**: 슬라이더로 Top-K 값 설정 (1-10개)
4. **분석 시작**: "🪔 지니의 마법 시작 ✨" 버튼 클릭
5. **결과 확인**: 
   - 목표 배우와 유사한 순서대로 지원자 랭킹 표시
   - 레퍼런스 배우는 **🎯 Target Reference** 배지로 자동 하이라이팅
   - 각 결과에 유사도 점수 표시

### 사용 시 주의사항

**이미지 업로드 요구사항**:
- ✅ **포맷**: `.jpg`, `.png`, `.webp` (권장)
- ❌ **비권장**: `.jfif` (일부 환경에서 얼굴 감지 실패 가능)
- ✅ **얼굴**: 명확한 정면 얼굴, 한 명만 나온 사진
- ✅ **해상도**: 최소 640px 이상 권장
- ❌ **파일 크기**: 최대 10MB

**레퍼런스 배우 입력**:
- 데이터셋에 있는 배우 이름 정확히 입력 (예: "고윤정", "강나언")
- 대소문자 구분 없음, 공백 자동 제거
- 존재하지 않는 배우 입력 시 조용히 무시됨

**결과 해석**:
- 점수 범위: 0.0 ~ 1.0 (코사인 유사도)
- 0.85 이상: 매우 유사
- 0.70 ~ 0.85: 유사
- 0.70 미만: 낮은 유사도
- **히어로 섹션**: Genie 캐릭터와 서비스 소개
- **입력 영역**: 레퍼런스 배우 이름 입력 필드
- **업로드 영역**: 드래그&드롭 존 + 파일 선택 버튼
- **설정**: Top-K 슬라이더 (기본값 5)
- **결과 영역**: 카드 형식으로 배우 정보, 점수, 이미지 표시

## API 엔드포인트

### 단일 이미지 매칭
```http
POST /match-actors?top_k=3
Content-Type: multipart/form-data

file: [이미지 파일]
```

### 배치 이미지 매칭 (레퍼런스 배우 포함)
```http
POST /match-actors-batch?top_k=5&reference_actor=송강호
Content-Type: multipart/form-data

files: [이미지 파일1]
files: [이미지 파일2]
files: [이미지 파일3]
```

**응답 예시**:
```json
{
  "items": [
    {
      "results": [
        {
          "name": "송강호",
          "score": 0.8523,
          "image_rel": "송강호/001.jpg",
          "image_url": "http://localhost:8000/actors/송강호/001.jpg",
          "is_reference": true
        },
        {
          "name": "이정재",
          "score": 0.7892,
          "image_rel": "이정재/001.jpg",
          "image_url": "http://localhost:8000/actors/이정재/001.jpg",
          "is_reference": false
        }
      ]
    }
  ]
}
```

**Query Parameters**:
- `top_k` (int, optional): 반환할 결과 개수 (기본값: 5)
- `reference_actor` (string, optional): 레퍼런스 배우 이름 (결과에서 `is_reference: true` 플래그 추가)

## 환경 변수

### 로컬 개발 환경

**프론트엔드 (`frontend/.env`)**:
```env
# 서버 사이드에서 FastAPI 호출 시 사용 (API Routes)
BACKEND_URL=http://localhost:8000

# 클라이언트 사이드에서 이미지 URL 생성 시 사용 (브라우저)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 프로덕션 배포 환경

**Vercel (프론트엔드)**:

Vercel 대시보드 → Settings → Environment Variables 추가:
```env
BACKEND_URL=https://your-railway-app.up.railway.app
NEXT_PUBLIC_BACKEND_URL=https://your-railway-app.up.railway.app
```

**Railway (백엔드)**:
- 환경 변수 설정 **불필요** (Railway가 자동으로 PORT 제공)

> **중요**: `.env` 파일은 Git에 커밋하지 마세요 (이미 `.gitignore`에 포함됨)

## 동작 원리

### 전체 플로우
1. **사용자 입력**: 레퍼런스 배우 이름 + 지원자 이미지 업로드
2. **얼굴 검출**: InsightFace가 업로드된 이미지에서 얼굴 영역 감지
3. **임베딩 생성**: 감지된 얼굴을 512차원 벡터로 변환
4. **유사도 계산**: 코사인 유사도로 302명의 배우 인덱스와 비교
5. **랭킹**: 유사도 점수가 높은 순서로 Top-K 배우 선택
6. **레퍼런스 플래깅**: `reference_actor`가 결과에 있으면 `is_reference: true` 추가
7. **결과 반환**: 프론트엔드에서 🎯 배지와 함께 시각화

### 핵심 알고리즘

**얼굴 임베딩 (InsightFace AuraFace-v1)**:
```python
# 이미지 → 512차원 정규화 벡터
embedding = model.get_embedding(face_image)  # shape: (512,)
normalized = embedding / np.linalg.norm(embedding)  # L2 정규화
```

**코사인 유사도 계산**:
```python
# 내적으로 코사인 유사도 계산 (벡터가 정규화되어 있으므로)
similarity = np.dot(query_vector, actor_vectors.T)  # shape: (N,)
top_k_indices = np.argsort(similarity)[::-1][:k]  # 상위 K개 선택
```

### 핵심 컴포넌트

**백엔드**:
- `embeddings.py`: CLIP ViT-B/32 모델로 이미지 → 512차원 벡터 변환
- `search.py`: NumPy 기반 코사인 유사도 계산 및 Top-K 검색
- `build_actor_index.py`: 배우별 이미지를 평균하여 대표 벡터 생성
- `main.py`: FastAPI 엔드포인트, CORS 설정, 레퍼런스 배우 로직

**프론트엔드**:
- `page.tsx`: Genie 테마 UI, 드래그&드롭, 진행률 표시, 레퍼런스 배지
- `route.ts`: API 프록시, 쿼리 파라미터 전달
- `globals.css`: Tailwind 커스텀 스타일 (Purple/Fuchsia/Amber)

## 테스트

```powershell
# 전체 테스트 실행
pytest -v

# 특정 테스트만 실행
pytest tests/test_api.py -v
```

## FAQ

### GPU가 필요한가요?
CPU만으로도 동작합니다. 최초 모델 로드 시 시간이 소요될 수 있습니다.

### 인덱스 없이 API를 호출하면?
`503 Service Unavailable` 에러를 반환합니다. 먼저 인덱스를 생성해야 합니다.

### CLIP 대신 다른 모델을 사용할 수 있나요?
네, `embeddings.py`를 수정하여 FaceNet, ArcFace, InsightFace 등으로 교체 가능합니다.

### 결과의 정확도를 높이려면?
- 배우 데이터셋의 이미지 품질과 수량을 늘리세요
- 얼굴 전용 임베딩 모델로 교체하세요
- `face_preprocess.py`의 얼굴 정렬 기능을 활성화하세요

## 배포

### 🚀 현재 운영 중인 프로덕션 환경

#### Backend (Railway)
- **URL**: https://geniecasting-production.up.railway.app
- **빌더**: Railpack (Nixpacks 후속 버전)
- **배포 방식**: GitHub Push → 자동 빌드 및 배포
- **인덱스**: 302명의 배우 임베딩 (배포 시 자동 생성)
- **상태 확인**: `/health`, `/index-status` 엔드포인트

#### Frontend (Vercel)
- **URL**: https://genie-casting.vercel.app
- **프레임워크**: Next.js 14.2.10 (App Router)
- **배포 방식**: GitHub Push → 자동 빌드 및 배포
- **환경 변수**: `BACKEND_URL`, `NEXT_PUBLIC_BACKEND_URL`

---

### Railway 배포 (백엔드)

1. [Railway](https://railway.app) 가입 및 로그인
2. **New Project** → **Deploy from GitHub repo** 선택
3. 이 저장소 선택
4. **Settings** 설정:
   - **Builder**: Railpack 자동 감지
   - **Root Directory**: 프로젝트 루트 (`/`)
   - **Environment Variables**: `PYTHONPATH=/app`
5. `nixpacks.toml` 파일 내용:
   ```toml
   [phases.setup]
   nixPkgs = ["python312", "gcc"]

   [phases.install]
   cmds = ["pip install -r requirements.txt"]

   [phases.build]
   cmds = ["python backend/scripts/build_actor_index_insightface.py"]

   [start]
   cmd = "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"

   [variables]
   PYTHONPATH = "/app"
   ```
6. 자동 배포 완료 대기 (빌드 시 302명 배우 인덱스 생성)
7. **Settings** → **Networking**에서 Public URL 확인 및 복사

> ⚠️ **중요**: 
> - `backend/app/models/` 폴더가 Git에 트래킹되어야 합니다
> - `.dockerignore` 파일이 있으면 제거하세요 (Railpack 강제 사용)
> - 프로덕션에서는 배포 시 자동으로 배우 인덱스가 생성됩니다

> 📝 상세 가이드: `DEPLOYMENT_GUIDE.md` Section 4-5 참고

### Vercel 배포 (프론트엔드)

1. [Vercel](https://vercel.com) 가입 및 로그인
2. **New Project** → GitHub 저장소 Import
3. **Framework Preset**: Next.js 자동 감지
4. **Root Directory**: `frontend` 입력
5. **Environment Variables** 추가:
   ```
   BACKEND_URL=https://your-railway-app.up.railway.app
   NEXT_PUBLIC_BACKEND_URL=https://your-railway-app.up.railway.app
   ```
6. **Deploy** 클릭
7. 배포 완료 후 Vercel URL 확인

> 📝 상세 가이드: `DEPLOYMENT_GUIDE.md` Section 6-7 참고

### 배포 후 테스트

**백엔드 상태 확인**:
```bash
# 헬스체크
curl https://your-railway-app.up.railway.app/health

# 인덱스 로드 확인 (actor_count: 302가 나와야 함)
curl https://your-railway-app.up.railway.app/index-status
```

**프론트엔드 테스트**:
1. Vercel URL 접속
2. 레퍼런스 배우 입력 (예: 고윤정)
3. `dataset/` 폴더에서 .jpg 또는 .png 파일 업로드
4. 결과 확인 (🎯 배지가 레퍼런스 배우에 표시됨)

### 배포 후 CORS 설정

현재 `backend/app/main.py`는 모든 오리진을 허용합니다:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

보안 강화를 위해 특정 도메인만 허용하려면:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://genie-casting.vercel.app",  # 프로덕션
        "http://localhost:3000"  # 로컬 테스트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### 일반적인 배포 문제 해결

| 오류 | 원인 | 해결책 |
|------|------|--------|
| "No module named 'backend.app.models'" | models/ 폴더가 Git에서 제외됨 | `.gitignore`에 `!backend/app/models/` 추가 |
| "No start command found" | nixpacks.toml 설정 누락 | `[start]` 섹션에 명시적 시작 명령 추가 |
| "얼굴을 감지할 수 없습니다" | .jfif 파일 또는 불명확한 얼굴 | .jpg/.png 파일 사용, 정면 얼굴 권장 |
| CORS 오류 | 백엔드 CORS 설정 문제 | `allow_origins=["*"]` 확인 |

### 배포 관련 문서
- `DEPLOYMENT_GUIDE.md`: 종합 배포 가이드 (10개 섹션, 40분)
- `DEPLOYMENT_CHECKLIST.md`: 빠른 배포 체크리스트 (25분)
- `PRE_DEPLOYMENT_CHECK.md`: 배포 전 연결 확인 리스트
- `IMAGE_COLLECTION_GUIDE.md`: 팀원용 이미지 수집 가이드
- `NAMING_RULES.md`: 파일/폴더 이름 규칙

## 향후 개선 사항

- [ ] 실시간 웹캠 촬영 및 분석
- [ ] 배우 데이터베이스 관리 대시보드
- [ ] 유사도 히트맵 시각화
- [ ] 다국어 지원 (영어, 일본어)
- [ ] 배우 프로필 상세 정보 표시 (필모그래피, 수상 경력)
- [ ] CSV/Excel 결과 내보내기
- [ ] 얼굴 전용 모델 옵션 (FaceNet, ArcFace, InsightFace)
- [ ] 사용자 피드백 기반 모델 재학습
- [ ] 배치 작업 큐 시스템 (Celery, Redis)
- [ ] 캐스팅 히스토리 저장 및 관리

## 문서

### 설치 및 설정
- `SETUP_GUIDE.md`: 초기 환경 설정 가이드
- `IMAGE_COLLECTION_GUIDE.md`: 팀원용 이미지 수집 가이드 (500+ 라인)
- `NAMING_RULES.md`: 파일/폴더 이름 규칙 (한글 배우명, 영문 파일명)

### 배포
- `DEPLOYMENT_GUIDE.md`: 종합 배포 가이드 (Railway + Vercel, 10개 섹션)
- `DEPLOYMENT_CHECKLIST.md`: 25분 빠른 배포 체크리스트
- `PRE_DEPLOYMENT_CHECK.md`: 배포 전 연결 확인 리스트

### API 문서
- Swagger UI: http://localhost:8000/docs (서버 실행 후)
- ReDoc: http://localhost:8000/redoc

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 문의

- **이메일**: disco922@naver.com
- **GitHub**: [YEAAAAAAAAAAp/Imagematch](https://github.com/YEAAAAAAAAAAp/Imagematch)

---

**Made with 🪔 by Genie Match Team**

*"소원을 말해봐, 완벽한 캐스팅을 이루어줄게!"*
