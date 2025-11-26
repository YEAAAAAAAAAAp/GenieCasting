# 🚀 배포 빠른 체크리스트

## 📋 배포 전 준비 (5분)

### 1. 로컬 테스트 완료 확인
```powershell
# 백엔드 테스트
curl http://localhost:8000/health

# 프론트엔드 확인
# 브라우저: http://localhost:3000
```

### 2. Git 푸시 완료
```powershell
git status
git push origin main
```

### 3. 배우 데이터베이스 준비
- [ ] `backend/app/data/embeddings.npy` 존재
- [ ] `backend/app/data/metadata.json` 존재
- [ ] `backend/app/data/actors/` 폴더에 이미지 존재

---

## 🎯 Railway 백엔드 배포 (10분)

### 1단계: Railway 설정
1. https://railway.app 접속 → GitHub 로그인
2. "New Project" → "Deploy from GitHub repo"
3. `Imagematch` 저장소 선택

### 2단계: 배포 설정
```
Root Directory: /
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

### 3단계: 환경 변수
```
PYTHONUNBUFFERED=1
```

### 4단계: 배우 데이터 업로드
**방법 A (간단)**: Git에 포함
```powershell
git add backend/app/data/
git commit -m "Add actor database"
git push
```

**방법 B (권장)**: 나중에 S3 연동

### 5단계: 배포 URL 복사
```
예: https://imagematch-production.up.railway.app
```

---

## 🌐 Vercel 프론트엔드 배포 (5분)

### 1단계: Vercel 설정
1. https://vercel.com 접속 → GitHub 로그인
2. "Add New..." → "Project"
3. `Imagematch` Import

### 2단계: 프로젝트 설정
```
Framework: Next.js
Root Directory: frontend
```

### 3단계: 환경 변수 (중요!)
```
BACKEND_URL=https://your-railway-url.railway.app
NEXT_PUBLIC_BACKEND_URL=https://your-railway-url.railway.app
```
**↑ Railway URL을 여기에 입력!**

### 4단계: Deploy 클릭

### 5단계: 배포 URL 확인
```
예: https://imagematch.vercel.app
```

---

## ✅ 배포 후 테스트 (5분)

### 백엔드 확인
```bash
# Health check
curl https://your-railway-url.railway.app/health

# 응답: {"status":"ok"}
```

### 프론트엔드 확인
1. Vercel URL 접속
2. 레퍼런스 배우 입력: "송강호"
3. 테스트 이미지 업로드
4. 결과 확인

---

## 🔧 문제 해결

### ❌ 백엔드 503 에러
→ 배우 데이터 누락: Git에 data 폴더 추가

### ❌ 프론트엔드 연결 실패
→ 환경 변수 확인: `NEXT_PUBLIC_BACKEND_URL` 올바른지 체크

### ❌ CORS 에러
→ `backend/app/main.py`에 Vercel URL 추가
```python
allow_origins=["https://your-vercel-url.vercel.app"]
```

---

## 📱 최종 확인

- [ ] 백엔드 Health Check 성공
- [ ] 프론트엔드 페이지 로드
- [ ] 레퍼런스 배우 입력 가능
- [ ] 이미지 업로드 작동
- [ ] 결과 정상 표시
- [ ] 배우 이미지 로드 확인

---

## 🎉 완료!

**백엔드**: https://your-railway-url.railway.app
**프론트엔드**: https://your-vercel-url.vercel.app

상세 가이드: `DEPLOYMENT_GUIDE.md` 참고
