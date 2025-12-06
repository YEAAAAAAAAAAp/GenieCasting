# Railway 배포 오류 해결 가이드

## 🔍 일반적인 Railway 배포 오류 원인

### 1. **Python 버전 불일치**
- **증상**: `ModuleNotFoundError`, `ImportError`
- **원인**: `nixpacks.toml`과 `runtime.txt`의 Python 버전 불일치
- **해결**: 
  ```toml
  # nixpacks.toml
  nixPkgs = ["python312"]  # Python 3.12
  ```
  ```
  # runtime.txt
  python-3.12.10
  ```

### 2. **포트 바인딩 오류**
- **증상**: `Application failed to respond`, `Connection refused`
- **원인**: Railway의 `$PORT` 환경변수 미사용
- **해결**:
  ```toml
  [start]
  cmd = "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"
  ```

### 3. **의존성 설치 실패**
- **증상**: `pip install` 중 타임아웃, `No module named 'xxx'`
- **원인**: 
  - 메모리 부족 (InsightFace는 큰 의존성)
  - 잘못된 패키지 버전
- **해결**:
  ```
  # requirements.txt에서 버전 명확히 지정
  numpy>=1.21.0,<2.0.0  # InsightFace는 numpy 2.0 미지원
  opencv-python-headless>=4.5.0,<4.11.0
  ```

### 4. **모델 다운로드 타임아웃**
- **증상**: 첫 배포 시 10분 이상 소요, 타임아웃
- **원인**: 408MB InsightFace 모델 다운로드
- **해결**:
  - Railway Volume 마운트: `/app/models`
  - 환경변수 설정: `HF_HOME=/app/models`
  - 재배포 시 모델 재사용

### 5. **메모리 부족 (OOM)**
- **증상**: `Killed`, `Exit code 137`
- **원인**: InsightFace 모델 + 배우 인덱스 로딩 시 메모리 초과
- **해결**:
  - Railway Pro 플랜 업그레이드 (8GB RAM)
  - 또는 배우 데이터베이스 크기 축소

### 6. **PYTHONPATH 설정 오류**
- **증상**: `ModuleNotFoundError: No module named 'backend'`
- **원인**: 프로젝트 루트 경로 인식 실패
- **해결**:
  ```toml
  [variables]
  PYTHONPATH = "/app"
  ```

### 7. **데이터 파일 누락**
- **증상**: `FileNotFoundError: backend/app/data/embeddings.npy`
- **원인**: Git에 데이터 파일 포함 안 됨
- **해결**:
  - `.gitignore`에서 `data/` 폴더 제외
  - 또는 빌드 시 데이터 생성 스크립트 실행

## 🛠️ 현재 GenieCasting 설정 확인

### ✅ 올바른 설정
```toml
# nixpacks.toml
[phases.setup]
nixPkgs = ["python312"]

[start]
cmd = "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"

[variables]
PYTHONPATH = "/app"
HF_HOME = "/app/models"
```

```
# runtime.txt
python-3.12.10
```

### ⚠️ 확인 필요 사항

1. **Railway Volume 마운트 여부**
   - Volume Name: `models-cache`
   - Mount Path: `/app/models`
   - Status: ✅ Connected

2. **환경변수 설정**
   ```
   HF_HOME=/app/models
   TRANSFORMERS_CACHE=/app/models
   ```

3. **데이터 파일 존재 여부**
   ```
   backend/app/data/
   ├── embeddings.npy (302명 배우, ~600KB)
   ├── metadata.json
   └── actors/ (배우 이미지)
   ```

## 📊 배포 로그 분석 방법

### 정상 배포 로그
```
✅ Installing dependencies from requirements.txt
✅ Successfully installed fastapi-0.115.5 uvicorn-0.32.0...
✅ 모델 파일 검증 완료: 5개 유효 ONNX 파일
✅ 배우 인덱스 로드 완료: 302명
🚀 서버 시작: 모델 사전 로딩 시작...
✅ 모델 사전 로딩 완료
INFO:     Application startup complete.
```

### 오류 발생 시 로그 패턴

#### 1. 포트 오류
```
ERROR: Application failed to respond
WARNING: Invalid HTTP request received
```
→ `--port $PORT` 확인

#### 2. 모듈 오류
```
ModuleNotFoundError: No module named 'backend'
```
→ `PYTHONPATH=/app` 확인

#### 3. 메모리 오류
```
Killed
Exit code: 137
```
→ Railway 플랜 업그레이드

#### 4. 타임아웃
```
Error: Deployment timed out after 15 minutes
```
→ Volume 마운트 및 모델 캐싱

## 🚀 즉각적인 해결 방법

### 방법 1: Railway 대시보드에서 재배포
1. Railway 프로젝트 접속
2. Backend 서비스 선택
3. "Deploy" → "Redeploy" 클릭
4. 로그 확인 (Deployments → Latest)

### 방법 2: 강제 재빌드
```bash
# .gitignore에 더미 파일 추가
echo "# Force rebuild" >> nixpacks.toml
git add nixpacks.toml
git commit -m "chore: force Railway rebuild"
git push
```

### 방법 3: 로컬에서 동일 환경 테스트
```bash
# Railway와 동일한 Python 버전 사용
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 로컬 서버 실행
export PYTHONPATH=$PWD
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## 📞 추가 지원

문제가 지속되면 다음 정보와 함께 문의:
1. Railway 배포 로그 전체 복사
2. `nixpacks.toml` 내용
3. `requirements.txt` 내용
4. Railway 환경변수 스크린샷 (민감 정보 제외)

**Railway 로그 확인 방법**:
1. Railway 대시보드 → Backend 서비스
2. "Deployments" 탭
3. 최신 배포 클릭
4. "View Logs" 버튼
5. 전체 로그 복사
