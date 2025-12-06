# Railway 배포 최종 가이드

## ✅ 코드 검증 완료

모든 필수 파일과 설정이 준비되었습니다:
- ✅ 설정 파일 (5개)
- ✅ 백엔드 구조 (4개)
- ✅ 배우 데이터 (302명)
- ✅ Python 의존성 (6개)
- ✅ Nixpacks 설정 (5개)
- ✅ Railway 설정 (2개)

## 🚨 **중요: Railway 대시보드에서 수동 설정 필요**

Railway 대시보드를 보니 **Builder가 Railpack으로 설정**되어 있습니다.
`railway.toml` 파일을 추가했지만, **수동으로 변경**해야 합니다.

### 📝 Railway 대시보드 설정 방법

1. **Railway 프로젝트 접속**
   ```
   https://railway.app/project/[your-project-id]
   ```

2. **Backend 서비스 선택**
   - GenieCasting 클릭

3. **Settings 탭 클릭**

4. **Builder 섹션에서 변경**
   - 현재: `Railpack` (Default)
   - 변경: **`Nixpacks`** 선택
   
   ![Railway Builder Settings](https://i.imgur.com/example.png)
   
   드롭다운에서:
   - ❌ Railpack (현재 선택됨)
   - ✅ **Nixpacks** ← 이것 선택
   - Dockerfile
   - (Deprecated) Nixpacks

5. **저장 후 재배포**
   - "Save" 버튼 클릭
   - 자동으로 재배포 시작

## 🔄 재배포 확인

### 성공적인 배포 로그
```
✅ using build driver nixpacks-v1.x.x  (Railpack 아님!)
✅ [phases.setup] nixPkgs = ["python312"]
✅ [phases.install] Installing dependencies...
✅ Successfully installed fastapi-0.115.5 uvicorn-0.32.0...
✅ [start] Starting with: uvicorn backend.app.main:app...
🚀 서버 시작: Railway 환경 검증...
   - PYTHONPATH: /app
   - HF_HOME: /app/models
   - PORT: 8000
   - 데이터 디렉토리: /app/backend/app/data
   - 데이터 디렉토리 존재: True
🚀 서버 시작: 모델 사전 로딩 시작...
✅ 모델 사전 로딩 완료
🚀 배우 인덱스 로딩 시작...
✅ 배우 인덱스 로드 완료: 302명
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 실패 시 로그 (Railpack 사용 중)
```
❌ using build driver railpack-v0.15.1  (잘못됨!)
❌ No start command was found
```

## 🧪 배포 후 테스트

### 1. 헬스체크
```bash
curl https://geniecasting-production.up.railway.app/health
# 응답: {"status":"ok","service":"genie-casting"}
```

### 2. 루트 엔드포인트
```bash
curl https://geniecasting-production.up.railway.app/
# 응답: {"service":"Genie Casting API","status":"running", ...}
```

### 3. 인덱스 상태
```bash
curl https://geniecasting-production.up.railway.app/index-status
# 응답: {"loaded":true,"actor_count":302,"has_index":true}
```

### 4. 이미지 매칭 테스트
```bash
curl -X POST https://geniecasting-production.up.railway.app/match-actors \
  -F "file=@test_image.jpg" \
  -F "top_k=3"
```

## 📌 중요 환경변수 확인

Railway 대시보드 → Variables 탭에서 확인:

```bash
PYTHONPATH=/app
HF_HOME=/app/models
TRANSFORMERS_CACHE=/app/models
PORT=(자동 설정)
```

## 🔧 문제 해결

### Builder 변경이 안 되는 경우
1. Railway CLI 설치
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. 프로젝트 연결 및 설정
   ```bash
   railway link
   railway service settings
   ```

3. 또는 수동으로 `.railway.json` 파일 생성
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     }
   }
   ```

### Vercel 연동 테스트
프론트엔드에서 백엔드 API 호출:
```typescript
// frontend/app/api/match-actors-batch/route.ts
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL
// https://geniecasting-production.up.railway.app
```

## 📊 예상 배포 시간

| 단계 | 소요 시간 |
|------|-----------|
| Builder 설정 변경 | 10초 |
| 첫 배포 (모델 다운로드) | 5-10분 |
| 재배포 (Volume 캐시) | 1-2분 |

## ⚡ 즉시 해야 할 일

1. **Railway 대시보드 접속**
2. **Settings → Builder → Nixpacks 선택**
3. **Save → 재배포 대기 (5-10분)**
4. **배포 로그 확인** (`using build driver nixpacks` 확인)
5. **헬스체크 테스트**

## 🎯 체크리스트

- [ ] Railway 대시보드에서 Builder를 Nixpacks로 변경
- [ ] 재배포 시작 확인
- [ ] 배포 로그에서 `nixpacks` 확인 (Railpack 아님)
- [ ] `/health` 엔드포인트 응답 확인
- [ ] `/index-status`에서 302명 확인
- [ ] Vercel 프론트엔드에서 API 테스트

## 📞 문제 발생 시

1. Railway 배포 로그 전체 복사
2. `check_deployment.py` 재실행
3. 스크린샷 공유:
   - Railway Settings → Builder 설정
   - Deployment Logs
   - Environment Variables

---

**배포 준비 완료! Railway 대시보드에서 Builder만 변경하면 됩니다.** 🚀
