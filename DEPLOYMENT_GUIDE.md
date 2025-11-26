# 🚀 Genie Match 배포 가이드

## 📋 배포 체크리스트

배포 전 반드시 확인해야 할 사항들입니다.

### ✅ 사전 준비 완료 상태
- [ ] 배우 데이터베이스 구축 완료 (backend/app/data/embeddings.npy, metadata.json)
- [ ] 로컬 테스트 완료 (localhost:3000)
- [ ] Git 커밋 & 푸시 완료
- [ ] 환경 변수 준비 완료

---

## 🎯 배포 아키텍처

### 권장 구조
```
Frontend (Vercel)
    ↓
Backend (Railway/Render/AWS)
    ↓
Actor Database (S3/Cloud Storage)
```

---

## 1️⃣ 백엔드 배포 (Railway 추천)

### Railway 배포 단계

#### 1-1. Railway 계정 생성
1. https://railway.app 접속
2. GitHub 계정으로 로그인
3. 새 프로젝트 생성

#### 1-2. 프로젝트 연결
```bash
# Railway CLI 설치 (선택사항)
npm i -g @railway/cli

# 로그인
railway login

# 프로젝트 초기화
cd C:\Users\disco\Desktop\LandingPage\Imagematch
railway init
```

#### 1-3. 배포 설정

**방법 A: Railway Dashboard 사용**
1. Railway Dashboard → "New Project" → "Deploy from GitHub repo"
2. Imagematch 저장소 선택
3. Root Directory: `/` (또는 `backend/`)
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

**방법 B: railway.json 파일 생성**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 1-4. 환경 변수 설정
Railway Dashboard → 프로젝트 → Variables에 추가:
```
PYTHONUNBUFFERED=1
PORT=8000
```

#### 1-5. 배우 데이터 업로드

**옵션 A: Git에 포함 (소규모)**
```bash
# .gitignore 수정하여 data 폴더 포함
# backend/app/data/ 폴더를 Git에 커밋
git add backend/app/data/
git commit -m "Add actor database"
git push
```

**옵션 B: Cloud Storage 사용 (권장, 대규모)**

1. **AWS S3 사용 예시**:
```python
# backend/app/services/search.py 수정
import boto3
import os

# S3에서 다운로드
s3 = boto3.client('s3')
s3.download_file('your-bucket', 'embeddings.npy', 'backend/app/data/embeddings.npy')
s3.download_file('your-bucket', 'metadata.json', 'backend/app/data/metadata.json')
```

2. **환경 변수 추가**:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your-bucket
```

#### 1-6. 배포 확인
```bash
# Railway 대시보드에서 제공하는 URL 확인
# 예: https://imagematch-production.up.railway.app

# Health check
curl https://your-railway-url.railway.app/health
```

---

## 2️⃣ 프론트엔드 배포 (Vercel)

### Vercel 배포 단계

#### 2-1. Vercel 계정 생성
1. https://vercel.com 접속
2. GitHub 계정으로 로그인

#### 2-2. 프로젝트 Import
1. Dashboard → "Add New..." → "Project"
2. GitHub에서 `Imagematch` 저장소 Import
3. Configure Project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (자동)
   - **Output Directory**: `.next` (자동)
   - **Install Command**: `npm install` (자동)

#### 2-3. 환경 변수 설정
Settings → Environment Variables에 추가:

```
BACKEND_URL=https://your-railway-url.railway.app
NEXT_PUBLIC_BACKEND_URL=https://your-railway-url.railway.app
```

**중요**: `NEXT_PUBLIC_BACKEND_URL`은 반드시 Railway에서 제공한 실제 백엔드 URL로 설정!

#### 2-4. 배포 실행
1. "Deploy" 버튼 클릭
2. 빌드 완료 대기 (약 2-5분)
3. 배포 URL 확인 (예: `https://imagematch.vercel.app`)

#### 2-5. 커스텀 도메인 설정 (선택)
1. Vercel Dashboard → Project → Settings → Domains
2. 도메인 추가 (예: `geniematch.com`)
3. DNS 설정에 따라 CNAME 레코드 추가

---

## 3️⃣ 배포 후 테스트

### 3-1. 백엔드 테스트
```bash
# Health Check
curl https://your-railway-url.railway.app/health

# API 문서 확인
# 브라우저에서 접속
https://your-railway-url.railway.app/docs
```

### 3-2. 프론트엔드 테스트
1. `https://your-vercel-url.vercel.app` 접속
2. 레퍼런스 배우 입력
3. 테스트 이미지 업로드
4. 분석 결과 확인

### 3-3. CORS 확인
만약 CORS 오류가 발생하면 `backend/app/main.py` 수정:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-url.vercel.app",
        "https://geniematch.com",  # 커스텀 도메인
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 4️⃣ 대안 배포 옵션

### 백엔드 대안

#### Render (Railway 대안)
```yaml
# render.yaml
services:
  - type: web
    name: imagematch-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

#### AWS EC2 (고급)
```bash
# EC2 인스턴스에서
sudo apt update
sudo apt install python3-pip python3-venv nginx

# 프로젝트 클론
git clone https://github.com/YEAAAAAAAAAAp/Imagematch.git
cd Imagematch

# 가상환경 설정
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Gunicorn으로 실행
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Nginx 리버스 프록시 설정
sudo nano /etc/nginx/sites-available/imagematch
```

### 프론트엔드 대안

#### Netlify
1. Netlify 대시보드 → "Add new site" → "Import from Git"
2. Build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/.next`

---

## 5️⃣ 성능 최적화

### 백엔드 최적화
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 캐싱 추가
from functools import lru_cache

@lru_cache(maxsize=100)
def get_actor_embedding(actor_name: str):
    # 자주 조회되는 배우 임베딩 캐싱
    pass
```

### 프론트엔드 최적화
```typescript
// frontend/next.config.mjs
export default {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'your-railway-url.railway.app',
      },
    ],
  },
  compress: true,
  swcMinify: true,
}
```

---

## 6️⃣ 모니터링 & 로깅

### Railway 모니터링
- Dashboard → Metrics에서 CPU, Memory, Network 확인
- Logs 탭에서 실시간 로그 확인

### Vercel 모니터링
- Analytics 탭에서 방문자, 성능 지표 확인
- Logs 탭에서 빌드 로그, 런타임 로그 확인

### 추가 모니터링 도구
- **Sentry**: 에러 트래킹
- **LogRocket**: 사용자 세션 리플레이
- **Google Analytics**: 웹 분석

---

## 7️⃣ 비용 예상

### Railway (백엔드)
- **Hobby Plan**: $5/월 (500시간 실행)
- **Pro Plan**: $20/월 (무제한)

### Vercel (프론트엔드)
- **Hobby**: 무료 (개인 프로젝트)
- **Pro**: $20/월 (팀/상업용)

### 총 예상 비용
- **개발/테스트**: $0-5/월
- **프로덕션**: $20-40/월

---

## 8️⃣ 보안 체크리스트

- [ ] 환경 변수로 민감 정보 관리
- [ ] HTTPS 사용 (Vercel/Railway 자동 제공)
- [ ] CORS 설정 확인
- [ ] Rate Limiting 추가
- [ ] API 키 인증 구현 (필요 시)
- [ ] 파일 업로드 크기 제한 확인
- [ ] SQL Injection 방지 (현재 프로젝트는 해당 없음)

---

## 9️⃣ CI/CD 자동화 (선택)

### GitHub Actions 설정
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID}}
          vercel-project-id: ${{ secrets.PROJECT_ID}}
```

---

## 🔟 문제 해결

### 백엔드가 시작되지 않음
```bash
# Railway Logs 확인
railway logs

# 일반적인 원인:
# 1. requirements.txt 설치 실패 → Python 버전 확인
# 2. PORT 변수 누락 → Railway에서 자동 제공
# 3. 배우 데이터 누락 → S3 또는 Git에서 확인
```

### 프론트엔드에서 백엔드 연결 실패
```bash
# 1. 환경 변수 확인
echo $NEXT_PUBLIC_BACKEND_URL

# 2. CORS 설정 확인
# 3. 백엔드 Health Check
curl https://your-backend-url/health
```

### 이미지 로드 실패
```javascript
// next.config.mjs에 백엔드 도메인 추가
images: {
  remotePatterns: [
    {
      protocol: 'https',
      hostname: 'your-railway-url.railway.app',
    },
  ],
}
```

---

## 📞 지원

- **이메일**: disco922@naver.com
- **GitHub Issues**: https://github.com/YEAAAAAAAAAAp/Imagematch/issues
- **문서**: README.md, SETUP_GUIDE.md

---

## 🎉 배포 완료 후

1. ✅ 프로덕션 URL 공유
2. ✅ 사용자 피드백 수집
3. ✅ 성능 모니터링
4. ✅ 정기적인 업데이트

**배포 성공을 축하합니다! 🚀✨**
