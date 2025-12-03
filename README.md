# Genie Casting - AI 기반 캐스팅 매칭 서비스 🪔✨

감독이 **레퍼런스 배우 이름을 입력**하고 지원자들의 사진을 업로드하면, **InsightFace AI가 얼굴 유사도를 분석하여 지원자를 자동으로 랭킹**해주는 혁신적인 캐스팅 솔루션입니다.

**🌐 라이브 데모**: https://genie-casting.vercel.app  
**📊 백엔드 API**: https://geniecasting-production.up.railway.app  
**📖 API 문서**: https://geniecasting-production.up.railway.app/docs

---

## 📋 목차

- [주요 특징](#주요-특징)
- [기술 스택](#기술-스택)
- [배포 아키텍처](#배포-아키텍처)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [사용 방법](#사용-방법)
- [API 엔드포인트](#api-엔드포인트)
- [환경 변수](#환경-변수)
- [동작 원리](#동작-원리)
- [배포](#배포)
- [FAQ](#faq)
- [문서](#문서)
- [라이선스](#라이선스)

---

## 주요 특징

### 🎯 레퍼런스 배우 기반 매칭
- 302명의 한국 유명 배우 데이터베이스 내장
- 레퍼런스 배우와의 유사도로 지원자 자동 랭킹
- 🎯 Target Reference 배지로 레퍼런스 배우 하이라이팅

### 🔮 최첨단 AI 얼굴 인식
- **InsightFace AuraFace-v1** 모델 (512차원 임베딩)
- 코사인 유사도 기반 정확한 매칭
- CPU 환경에서도 빠른 추론 속도

### ⚡ 실시간 배치 처리
- 여러 지원자 이미지 동시 분석
- 실시간 진행률 표시 (0~100%)
- 비동기 처리로 빠른 응답

### ✨ Genie 테마 UI/UX
- Purple/Fuchsia/Amber 그라데이션 디자인
- 드래그&드롭 파일 업로드
- 반응형 디자인 (모바일/태블릿/데스크톱)
- 부드러운 애니메이션 효과

### 📊 유연한 설정
- Top-K 슬라이더 (1~10개)
- 이미지 미리보기 및 삭제
- 결과 카드 형식 표시

---

## 기술 스택

### 백엔드 (Python 3.12.10)
```
FastAPI 0.115.5          - REST API 프레임워크
InsightFace 0.7.3+       - 얼굴 인식 임베딩 모델
ONNX Runtime 1.10+       - 모델 추론 최적화
OpenCV 4.10              - 이미지 전처리
NumPy 1.26.x (<2.0)      - 벡터 연산 (InsightFace 호환)
Uvicorn 0.32.0           - ASGI 웹 서버
```

### 프론트엔드
```
Next.js 14.2.10          - React 프레임워크 (App Router)
TypeScript 5.x           - 정적 타입 검사
Tailwind CSS 3.x         - 유틸리티 CSS 프레임워크
```

### 인프라
```
Railway (Railpack)       - 백엔드 호스팅
Vercel                   - 프론트엔드 호스팅 + CDN
GitHub Actions           - CI/CD 자동 배포
```

---

## 배포 아키텍처

```
┌──────────────────┐
│  사용자 브라우저  │
└────────┬─────────┘
         │
         ↓
┌─────────────────────────────┐
│ Vercel - Next.js Frontend   │
│ genie-casting.vercel.app    │
└────────┬────────────────────┘
         │ /api/match-actors-batch
         │ (API Route Proxy)
         ↓
┌──────────────────────────────────┐
│ Railway - FastAPI Backend        │
│ geniecasting-production.up...   │
└────────┬─────────────────────────┘
         │
         ↓
┌────────────────────────────┐
│ InsightFace AuraFace-v1    │
│ (512차원 얼굴 임베딩)       │
└────────┬───────────────────┘
         │
         ↓
┌──────────────────────────────┐
│ 배우 인덱스                   │
│ - embeddings.npy (302×512)   │
│ - metadata.json              │
│ - actors/ (이미지 폴더)      │
└──────────────────────────────┘
```

### 배포 상태
- ✅ **Railway 백엔드**: 정상 작동 (302명 배우 인덱스 로드 완료)
- ✅ **Vercel 프론트엔드**: 정상 배포 (환경변수 설정 완료)
- ✅ **CORS 설정**: 모든 origin 허용
- ✅ **CI/CD**: GitHub Push → 자동 빌드 및 배포

---

## 프로젝트 구조

```
GenieCasting/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI 앱 & 엔드포인트
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py               # Pydantic 데이터 모델
│   │   ├── services/
│   │   │   ├── embeddings.py            # InsightFace 임베딩 생성
│   │   │   ├── face_preprocess.py       # 얼굴 전처리 (옵션)
│   │   │   └── search.py                # 배우 인덱스 검색
│   │   └── data/                        # 생성된 인덱스 (gitignore)
│   │       ├── embeddings.npy           # 배우 임베딩 벡터
│   │       ├── metadata.json            # 배우 메타데이터
│   │       └── actors/                  # 배우 대표 이미지
│   └── scripts/
│       ├── build_actor_index_insightface.py  # 인덱스 생성 스크립트
│       └── build_index_from_cache.py         # 캐시로부터 인덱스 생성
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                     # 메인 페이지 (Genie UI)
│   │   ├── layout.tsx                   # 레이아웃 컴포넌트
│   │   ├── globals.css                  # Tailwind + 커스텀 스타일
│   │   └── api/
│   │       └── match-actors-batch/
│   │           └── route.ts             # API 프록시 라우트
│   ├── public/
│   │   └── genie-clean.png              # 지니 로고
│   ├── next.config.mjs                  # Next.js 설정
│   ├── tailwind.config.js               # Tailwind 커스텀 테마
│   └── package.json                     # npm 의존성
│
├── dataset/                             # 배우 데이터셋 (302명)
│   ├── embeddings/                      # 사전 생성된 임베딩 캐시
│   │   ├── 강나언/
│   │   │   ├── 001.json
│   │   │   └── ...
│   │   └── ...
│   ├── 강나언/
│   │   ├── 001.jpg
│   │   └── ...
│   └── ...
│
├── requirements.txt                     # Python 패키지 목록
├── nixpacks.toml                        # Railway 빌드 설정
├── runtime.txt                          # Python 버전 (3.12.10)
├── .gitignore                           # Git 제외 파일
├── README.md                            # 프로젝트 문서 (이 파일)
└── SETUP_GUIDE.md                       # 설치 가이드
```

---

## 설치 및 실행

### 1. 사전 요구사항

- **Python**: 3.10 이상 (권장: 3.12.10)
- **Node.js**: 18.x 이상
- **Git**: 버전 관리
- **Visual C++ Build Tools** (Windows): InsightFace 컴파일용

### 2. 저장소 클론

```bash
git clone https://github.com/YEAAAAAAAAAAp/GenieCasting.git
cd GenieCasting
```

### 3. 백엔드 설정

#### 가상환경 생성 (Windows PowerShell)

```powershell
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt
```

#### 배우 인덱스 생성

**중요**: 프로덕션(Railway)에서는 자동으로 인덱스가 생성됩니다. 로컬 개발 시에만 필요합니다.

```powershell
# PYTHONPATH 설정
$env:PYTHONPATH = (Get-Location).Path

# dataset/ 폴더로부터 인덱스 생성
python backend/scripts/build_actor_index_insightface.py --dataset-dir dataset --clusters-per-actor 1
```

**생성 결과**: `backend/app/data/` 폴더에 다음 파일 생성
- `embeddings.npy`: 302명 × 512차원 벡터
- `metadata.json`: 배우 이름, 이미지 경로
- `actors/`: 배우별 대표 이미지 폴더

#### 백엔드 서버 실행

```powershell
# 가상환경 활성화 (필수)
.\.venv\Scripts\Activate.ps1

# 서버 시작
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**접속 확인**:
- API 문서: http://localhost:8000/docs
- 인덱스 상태: http://localhost:8000/index-status
  ```json
  {
    "loaded": true,
    "actor_count": 302,
    "has_index": true
  }
  ```

### 4. 프론트엔드 설정

새 터미널을 열고:

```powershell
cd frontend

# 환경변수 설정 (.env.local 파일 생성)
@"
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
"@ | Out-File -FilePath .env.local -Encoding utf8

# npm 패키지 설치
npm install

# 개발 서버 시작
npm run dev
```

**접속**: http://localhost:3000

---

## 사용 방법

### 기본 워크플로우

1. **레퍼런스 배우 입력**
   - 캐스팅하고 싶은 유명 배우 이름 입력 (예: 송강호, 고윤정)
   - 데이터베이스에 있는 302명의 배우 중 선택

2. **지원자 사진 업로드**
   - 드래그&드롭 또는 파일 선택 버튼
   - 여러 장 동시 업로드 가능
   - 지원 포맷: `.jpg`, `.png`, `.webp`

3. **결과 개수 설정**
   - 슬라이더로 Top-K 값 조절 (1~10개)
   - 상위 몇 명의 지원자를 보여줄지 설정

4. **분석 시작**
   - "🪔 지니의 마법 시작 ✨" 버튼 클릭
   - 실시간 진행률 표시

5. **결과 확인**
   - 레퍼런스 배우와의 유사도 순으로 지원자 랭킹
   - 🎯 Target Reference 배지로 레퍼런스 배우 표시
   - 각 결과에 유사도 점수 표시 (0.0 ~ 1.0)

### 이미지 업로드 요구사항

**✅ 권장사항**:
- 포맷: `.jpg`, `.png`, `.webp`
- 해상도: 최소 640×640px 이상
- 얼굴: 명확한 정면 얼굴, 한 명만 나온 사진
- 파일 크기: 최대 10MB

**❌ 비권장**:
- `.jfif` 포맷 (일부 환경에서 얼굴 감지 실패)
- 측면 얼굴, 여러 명이 나온 사진
- 저해상도 이미지 (<300px)

### 결과 해석

**유사도 점수 범위** (코사인 유사도):
- `0.85 이상`: 매우 유사 (거의 동일한 얼굴형)
- `0.70 ~ 0.85`: 유사 (비슷한 인상)
- `0.70 미만`: 낮은 유사도

**레퍼런스 배우 표시**:
- 🎯 배지가 있는 카드가 목표 배우
- 다른 카드들은 유사도 순으로 정렬된 지원자

---

## API 엔드포인트

### 1. 헬스 체크

```http
GET /health
```

**응답**:
```json
{
  "status": "ok"
}
```

### 2. 인덱스 상태 확인

```http
GET /index-status
```

**응답**:
```json
{
  "loaded": true,
  "actor_count": 302,
  "has_index": true
}
```

### 3. 단일 이미지 매칭

```http
POST /match-actors?top_k=3
Content-Type: multipart/form-data

file: [이미지 파일]
```

**Query Parameters**:
- `top_k` (int, 선택): 반환할 상위 K개 (기본값: 3, 범위: 1~10)

**응답**:
```json
{
  "results": [
    {
      "name": "송강호",
      "score": 0.8523,
      "image_url": "/actors/송강호/001.jpg"
    },
    {
      "name": "이정재",
      "score": 0.7892,
      "image_url": "/actors/이정재/001.jpg"
    }
  ]
}
```

### 4. 배치 이미지 매칭 (레퍼런스 모드)

```http
POST /match-actors-batch?top_k=5&reference_actor=송강호
Content-Type: multipart/form-data

files: [이미지 파일1]
files: [이미지 파일2]
files: [이미지 파일3]
```

**Query Parameters**:
- `top_k` (int, 선택): 반환할 지원자 수 (기본값: 3, 범위: 1~50)
- `reference_actor` (string, 선택): 레퍼런스 배우 이름

**응답 (레퍼런스 모드)**:
```json
{
  "items": [
    {
      "filename": "applicant1.jpg",
      "results": [
        {
          "name": "송강호",
          "score": 0.8523,
          "image_url": "/actors/송강호/001.jpg",
          "is_reference": true
        }
      ],
      "reference_score": 0.8523
    },
    {
      "filename": "applicant2.jpg",
      "results": [
        {
          "name": "송강호",
          "score": 0.7892,
          "image_url": "/actors/송강호/001.jpg",
          "is_reference": true
        }
      ],
      "reference_score": 0.7892
    }
  ],
  "ranked_by_reference": [
    {
      "filename": "applicant1.jpg",
      "reference_score": 0.8523
    },
    {
      "filename": "applicant2.jpg",
      "reference_score": 0.7892
    }
  ],
  "reference_actor": "송강호"
}
```

**응답 (일반 모드, reference_actor 미지정)**:
```json
{
  "items": [
    {
      "filename": "applicant1.jpg",
      "results": [
        {
          "name": "송강호",
          "score": 0.8523,
          "image_url": "/actors/송강호/001.jpg",
          "is_reference": false
        },
        {
          "name": "이정재",
          "score": 0.7892,
          "image_url": "/actors/이정재/001.jpg",
          "is_reference": false
        },
        {
          "name": "전지현",
          "score": 0.7654,
          "image_url": "/actors/전지현/001.jpg",
          "is_reference": false
        }
      ]
    }
  ]
}
```

---

## 환경 변수

### 로컬 개발 환경

**백엔드** (선택사항):
```env
# 기본값이 있으므로 설정 불필요
PORT=8000
```

**프론트엔드** (`frontend/.env.local`):
```env
# 서버 사이드 API 호출 (API Routes)
BACKEND_URL=http://localhost:8000

# 클라이언트 사이드 이미지 URL (브라우저)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 프로덕션 환경

**Railway (백엔드)**:
- 환경변수 설정 **불필요** (Railway가 자동으로 `PORT` 제공)

**Vercel (프론트엔드)**:

Vercel 대시보드 → Settings → Environment Variables:
```env
BACKEND_URL=https://geniecasting-production.up.railway.app
NEXT_PUBLIC_BACKEND_URL=https://geniecasting-production.up.railway.app
```

> ⚠️ **주의**: `.env.local` 파일은 Git에 커밋하지 마세요 (`.gitignore`에 포함됨)

---

## 동작 원리

### 전체 플로우

```
┌─────────────────┐
│ 1. 사용자 입력   │
│ - 레퍼런스 배우  │
│ - 지원자 이미지  │
└────────┬────────┘
         │
         ↓
┌─────────────────────┐
│ 2. 얼굴 검출        │
│ InsightFace가       │
│ 얼굴 영역 감지      │
└────────┬────────────┘
         │
         ↓
┌─────────────────────┐
│ 3. 임베딩 생성      │
│ 512차원 벡터로 변환 │
└────────┬────────────┘
         │
         ↓
┌─────────────────────────┐
│ 4. 유사도 계산          │
│ 코사인 유사도로         │
│ 302명 배우와 비교       │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│ 5. 랭킹 & 플래깅        │
│ - 유사도 순 정렬        │
│ - 레퍼런스 배우 표시    │
└────────┬────────────────┘
         │
         ↓
┌─────────────────┐
│ 6. 결과 반환    │
│ 🎯 배지 + 점수  │
└─────────────────┘
```

### 핵심 알고리즘

#### 1. 얼굴 임베딩 (InsightFace AuraFace-v1)

```python
# 이미지 → 512차원 정규화 벡터
embedding = model.get_embedding(face_image)  # shape: (512,)
normalized = embedding / np.linalg.norm(embedding)  # L2 정규화
```

#### 2. 코사인 유사도 계산

```python
# 내적으로 코사인 유사도 계산 (벡터가 정규화되어 있으므로)
similarity = np.dot(query_vector, actor_vectors.T)  # shape: (N,)
top_k_indices = np.argsort(similarity)[::-1][:k]  # 상위 K개 선택
```

#### 3. 레퍼런스 배우 검색

```python
# 레퍼런스 배우 이름으로 인덱스에서 검색
for idx, meta in enumerate(metadata):
    if meta['name'] == reference_actor:
        score = similarity[idx]
        return (idx, score)
```

### 핵심 컴포넌트

**백엔드**:
- `embeddings.py`: InsightFace AuraFace-v1 모델로 얼굴 → 512차원 벡터
- `search.py`: NumPy 기반 코사인 유사도 및 Top-K 검색
- `main.py`: FastAPI 엔드포인트, 레퍼런스 모드/일반 모드 처리
- `schemas.py`: Pydantic 데이터 모델 (MatchResult, BatchMatchResponse 등)

**프론트엔드**:
- `page.tsx`: Genie 테마 UI, 드래그&드롭, 진행률 표시, 🎯 배지
- `route.ts`: API 프록시, 쿼리 파라미터 전달
- `globals.css`: Tailwind 커스텀 스타일 (Purple/Fuchsia/Amber)

---

## 배포

### 🚀 현재 운영 중인 프로덕션 환경

#### Backend (Railway)
- **URL**: https://geniecasting-production.up.railway.app
- **빌더**: Railpack (Nixpacks 후속)
- **배포 방식**: GitHub Push → 자동 빌드
- **인덱스**: 302명 배우 임베딩 (배포 시 자동 생성)

#### Frontend (Vercel)
- **URL**: https://genie-casting.vercel.app
- **프레임워크**: Next.js 14.2.10 (App Router)
- **배포 방식**: GitHub Push → 자동 빌드

---

### Railway 배포 (백엔드)

#### 1. Railway 프로젝트 생성

1. [Railway](https://railway.app) 가입 및 로그인
2. **New Project** → **Deploy from GitHub repo**
3. 이 저장소 선택

#### 2. 빌드 설정

`nixpacks.toml` 파일 (프로젝트 루트):
```toml
[phases.setup]
nixPkgs = ["python312", "gcc"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = [
  "python backend/scripts/build_index_from_cache.py"
]

[start]
cmd = "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"

[variables]
PYTHONPATH = "/app"
```

#### 3. 환경 변수 (자동 설정)

Railway가 자동으로 `PORT` 환경변수를 제공하므로 추가 설정 불필요

#### 4. 배포 확인

```bash
# 헬스체크
curl https://geniecasting-production.up.railway.app/health

# 인덱스 상태 (actor_count: 302 확인)
curl https://geniecasting-production.up.railway.app/index-status
```

---

### Vercel 배포 (프론트엔드)

#### 1. Vercel 프로젝트 생성

1. [Vercel](https://vercel.com) 가입 및 로그인
2. **New Project** → GitHub 저장소 Import
3. **Framework Preset**: Next.js 자동 감지
4. **Root Directory**: `frontend` 입력

#### 2. 환경 변수 설정

Vercel 대시보드 → Settings → Environment Variables:

```
BACKEND_URL=https://geniecasting-production.up.railway.app
NEXT_PUBLIC_BACKEND_URL=https://geniecasting-production.up.railway.app
```

#### 3. 배포 및 확인

- **Deploy** 클릭
- 배포 완료 후 Vercel URL 접속
- 레퍼런스 배우 입력 후 이미지 업로드 테스트

---

### CORS 설정 (보안 강화)

현재는 모든 오리진 허용 (`allow_origins=["*"]`):

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

프로덕션에서는 특정 도메인만 허용 권장:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://genie-casting.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

### 배포 문제 해결

| 오류 | 원인 | 해결책 |
|------|------|--------|
| `No module named 'backend.app.models'` | models/ 폴더 누락 | `.gitignore`에 `!backend/app/models/` 추가 |
| `No start command found` | nixpacks.toml 설정 누락 | `[start]` 섹션에 uvicorn 명령 추가 |
| `얼굴을 감지할 수 없습니다` | 불명확한 얼굴 이미지 | .jpg/.png 정면 얼굴 사용 |
| CORS 오류 | 백엔드 CORS 설정 문제 | `allow_origins` 확인 |
| `503 Service Unavailable` | 인덱스 미생성 | 배포 로그에서 build 단계 확인 |

---

## FAQ

### Q1. GPU가 필요한가요?
**A**: CPU만으로도 동작합니다. InsightFace는 ONNX Runtime을 사용하여 CPU에서도 빠른 추론이 가능합니다.

### Q2. 인덱스 없이 API를 호출하면?
**A**: `503 Service Unavailable` 에러를 반환합니다. 먼저 `build_actor_index_insightface.py` 스크립트로 인덱스를 생성해야 합니다.

### Q3. 결과의 정확도를 높이려면?
**A**: 
- 배우 데이터셋의 이미지 품질과 수량 증가
- 얼굴 전용 임베딩 모델로 교체 (ArcFace, FaceNet 등)
- `face_preprocess.py`의 얼굴 정렬 기능 활성화

### Q4. 배우 데이터베이스를 추가하려면?
**A**: 
1. `dataset/` 폴더에 새 배우 폴더 생성 (예: `dataset/새배우/`)
2. 배우의 사진 10장 이상 추가 (001.jpg, 002.jpg, ...)
3. `build_actor_index_insightface.py` 재실행

### Q5. Windows에서 InsightFace 설치 오류가 발생하면?
**A**: Visual C++ Build Tools를 설치하세요:
1. [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/) 다운로드
2. "Desktop development with C++" 워크로드 선택
3. 설치 후 `pip install -r requirements.txt` 재실행

### Q6. `.jfif` 파일이 지원되나요?
**A**: 기술적으로는 지원하지만, 일부 환경에서 얼굴 감지가 실패할 수 있습니다. `.jpg` 또는 `.png` 포맷 권장.

---

## 문서

### 설치 및 설정
- `SETUP_GUIDE.md`: 초기 환경 설정 가이드
- `IMAGE_COLLECTION_GUIDE.md`: 배우 이미지 수집 가이드
- `NAMING_RULES.md`: 파일/폴더 이름 규칙

### 배포
- `DEPLOYMENT_GUIDE.md`: Railway + Vercel 종합 배포 가이드
- `DEPLOYMENT_CHECKLIST.md`: 25분 빠른 배포 체크리스트
- `PRE_DEPLOYMENT_CHECK.md`: 배포 전 연결 확인 리스트

### API 문서
- Swagger UI: https://geniecasting-production.up.railway.app/docs
- ReDoc: https://geniecasting-production.up.railway.app/redoc

---

## 라이선스

MIT License

Copyright (c) 2025 Genie Casting Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

### 기여 방법
1. 이 저장소를 Fork
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

---

## 문의

- **이메일**: disco922@naver.com
- **GitHub**: [YEAAAAAAAAAAp/GenieCasting](https://github.com/YEAAAAAAAAAAp/GenieCasting)
- **이슈**: [GitHub Issues](https://github.com/YEAAAAAAAAAAp/GenieCasting/issues)

---

## 향후 개선 사항

- [ ] 실시간 웹캠 촬영 및 분석
- [ ] 배우 데이터베이스 관리 대시보드
- [ ] 유사도 히트맵 시각화
- [ ] 다국어 지원 (영어, 일본어, 중국어)
- [ ] 배우 프로필 상세 정보 (필모그래피, 수상 경력)
- [ ] CSV/Excel 결과 내보내기
- [ ] 사용자 피드백 기반 모델 재학습
- [ ] 배치 작업 큐 시스템 (Celery, Redis)
- [ ] 캐스팅 히스토리 저장 및 관리
- [ ] 모바일 앱 버전 (React Native)

---

**Made with 🪔 by Genie Casting Team**

*"소원을 말해봐, 완벽한 캐스팅을 이루어줄게!"*
