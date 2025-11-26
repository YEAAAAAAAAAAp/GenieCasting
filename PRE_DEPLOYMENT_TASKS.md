# 배포 전 작업 체크리스트 (간소화 버전)

> **현재 상태**: 배우 이미지 데이터셋 5,000장 준비 완료 ✅

---

## 🚀 1단계: 배우 인덱스 생성 (10분)

```powershell
# 1. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 2. 인덱스 생성 (dataset_production 폴더에 5,000장 이미지 있다고 가정)
$env:PYTHONPATH="C:\Users\disco\Desktop\LandingPage\Imagematch"
.\.venv\Scripts\python.exe backend\scripts\build_actor_index_insightface.py --dataset-dir dataset_production

# ✅ 완료 확인: "배우 인덱스 생성 완료: N명" 메시지 확인
```

---

## 🧪 2단계: 로컬 테스트 (5분)

```powershell
# 1. 백엔드 서버 시작
$env:PYTHONPATH="C:\Users\disco\Desktop\LandingPage\Imagematch"
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000" -NoNewWindow

# 2. 새 터미널에서 프론트엔드 시작
cd frontend
npm run dev

# 3. 브라우저에서 테스트
# http://localhost:3000 접속 → 배우 이름 입력 → 이미지 업로드 → 결과 확인
```

**체크리스트:**
- [ ] 배우 매칭 결과가 정상적으로 표시되는가?
- [ ] 레퍼런스 배우에 🎯 배지가 표시되는가?
- [ ] 이미지가 정상 로드되는가?

---

## 📦 3단계: Git 커밋 (3분)

```powershell
# 1. .gitignore 확인 (dataset은 Git에 포함하지 않음)
cat .gitignore

# 2. 변경사항만 커밋 (소스 코드만)
git status
git add backend/ frontend/ requirements.txt README.md
git commit -m "chore: Prepare for production deployment"
git push origin main
```

**참고:** `dataset_production/` 폴더는 Git에 추가하지 않습니다 (용량 큼).

---

## ☁️ 4단계: Railway 백엔드 배포 (15분)

### 4-1. Railway 프로젝트 생성
1. https://railway.app → 로그인
2. **New Project** → **Deploy from GitHub repo**
3. 저장소 선택: `YEAAAAAAAAAAp/Imagematch`

### 4-2. Railway 설정
**Settings 탭:**
- **Root Directory**: `backend`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 4-3. 배우 데이터 업로드
⚠️ **5,000장 이미지는 Railway Volume 사용 필요:**

```powershell
# Railway CLI 설치 (최초 1회)
npm i -g @railway/cli

# Railway 로그인
railway login

# Volume 생성 및 데이터 업로드
railway volume create --name actors-dataset --mount /app/dataset_production
railway volume upload dataset_production /app/dataset_production
```

### 4-4. Start Command 수정
Railway **Settings** → **Start Command**:
```bash
python scripts/build_actor_index_insightface.py --dataset-dir /app/dataset_production && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 4-5. 배포 확인
- **Deployments** 탭에서 로그 확인
- **Settings** → **Networking** → **Public URL** 복사
  - 예: `https://imagematch-production-abc.up.railway.app`

```powershell
# API 테스트
Invoke-RestMethod -Uri "https://imagematch-production-abc.up.railway.app/health"
```

---

## 🌐 5단계: Vercel 프론트엔드 배포 (10분)

### 5-1. Vercel 프로젝트 생성
1. https://vercel.com → 로그인
2. **Add New...** → **Project**
3. `YEAAAAAAAAAAp/Imagematch` 저장소 선택

### 5-2. Vercel 설정
**Configure Project:**
- **Root Directory**: `frontend`
- **Environment Variables** 추가:
  ```
  BACKEND_URL=https://imagematch-production-abc.up.railway.app
  NEXT_PUBLIC_BACKEND_URL=https://imagematch-production-abc.up.railway.app
  ```

### 5-3. 배포
- **Deploy** 클릭
- 완료 후 Vercel URL 복사: `https://imagematch.vercel.app`

---

## 🔧 6단계: CORS 업데이트 (3분)

**파일:** `backend/app/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://imagematch.vercel.app",  # ← 실제 Vercel URL로 변경
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

```powershell
# 커밋 & 푸시 (Railway 자동 재배포됨)
git add backend/app/main.py
git commit -m "fix: Update CORS for production"
git push origin main
```

---

## ✅ 7단계: 최종 테스트 (5분)

### 프로덕션 환경 테스트
1. **백엔드 API**
   ```powershell
   Invoke-RestMethod -Uri "https://imagematch-production-abc.up.railway.app/health"
   ```

2. **프론트엔드**
   - `https://imagematch.vercel.app` 접속
   - 레퍼런스 배우 입력 (실제 배우 이름)
   - 이미지 업로드 및 매칭 테스트

**체크리스트:**
- [ ] Health check API 정상 응답
- [ ] 프론트엔드 정상 로드
- [ ] 배우 매칭 기능 작동
- [ ] 레퍼런스 배우 하이라이팅 정상
- [ ] 이미지 정상 표시

---

## 📊 완료 체크리스트

- [ ] 1단계: 배우 인덱스 생성 완료
- [ ] 2단계: 로컬 테스트 통과
- [ ] 3단계: Git 커밋 완료
- [ ] 4단계: Railway 백엔드 배포 완료
- [ ] 5단계: Vercel 프론트엔드 배포 완료
- [ ] 6단계: CORS 업데이트 완료
- [ ] 7단계: 프로덕션 최종 테스트 통과

---

## 🆘 문제 해결

### Railway 배포 실패
```powershell
# 로그 확인
railway logs

# 주요 원인:
# - Volume 마운트 안 됨 → railway volume list 확인
# - 인덱스 생성 실패 → 데이터셋 경로 확인 (/app/dataset_production)
```

### Vercel 빌드 실패
- Root Directory가 `frontend`로 설정되었는지 확인
- 환경 변수 (BACKEND_URL) 정확히 입력되었는지 확인

### CORS 에러
- `backend/app/main.py`에 Vercel URL 추가했는지 확인
- URL 끝에 슬래시(/) 없는지 확인

---

**예상 소요 시간**: 총 50분
- 인덱스 생성: 10분
- 로컬 테스트: 5분
- Git 커밋: 3분
- Railway 배포: 15분
- Vercel 배포: 10분
- CORS 업데이트: 3분
- 최종 테스트: 5분

✅ **완료!**
