# 모델 다운로드 문제 해결 (2025-12-01)

## 🔍 문제 상황

배포 환경에서 "코드에 모델을 다운받는 부분이 없다"는 피드백을 받았습니다.

### 기존 동작 방식의 문제점

1. **모델 다운로드 시점**: 첫 API 요청이 들어왔을 때 (런타임)
2. **위치**: `backend/app/services/embeddings.py`의 `get_insightface_model()` 함수
3. **문제**: 
   - 빌드 단계에서는 모델이 다운로드되지 않음
   - 첫 요청 시 모델 다운로드로 인한 긴 응답 시간
   - 네트워크 문제 시 서비스 실패 가능성

```python
# 기존 코드 (embeddings.py)
@lru_cache(maxsize=1)
def get_insightface_model(ctx_id: int = -1) -> FaceAnalysis:
    # 모델 다운로드 로직
    model_dir = Path("models/auraface")
    if not model_dir.exists():
        snapshot_download("fal/AuraFace-v1", local_dir=str(model_dir))  # 첫 요청 시 실행
    # ...
```

## ✅ 해결 방법

### 1. 명시적 모델 다운로드 스크립트 생성

**새 파일**: `backend/scripts/download_models.py`

```python
"""
배포 환경에서 InsightFace 모델을 사전 다운로드하는 스크립트
Railway 빌드 단계에서 실행하여 모델을 미리 다운로드합니다.
"""
from pathlib import Path
from huggingface_hub import snapshot_download

def main():
    model_dir = Path("models/auraface")
    
    # 모델이 이미 존재하면 스킵
    if model_dir.exists() and any(model_dir.iterdir()):
        print(f"✅ 모델이 이미 존재합니다: {model_dir}")
        return
    
    # HuggingFace Hub에서 다운로드
    print("📥 HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중...")
    snapshot_download(
        "fal/AuraFace-v1", 
        local_dir=str(model_dir),
        local_dir_use_symlinks=False  # Railway/Vercel 호환성
    )
    
    print("✅ 모델 다운로드 완료!")
```

### 2. 빌드 설정 수정

**파일**: `nixpacks.toml`

```diff
  [phases.build]
- cmds = ["python backend/scripts/build_actor_index_insightface.py --dataset dataset/ --clusters 1"]
+ cmds = [
+   "python backend/scripts/download_models.py",                                      # 1. 모델 먼저 다운로드
+   "python backend/scripts/build_actor_index_insightface.py --dataset-dir dataset"  # 2. 인덱스 생성
+ ]
```

### 3. 모델 로딩 로직 개선

**파일**: `backend/app/services/embeddings.py`

```python
@lru_cache(maxsize=1)
def get_insightface_model(ctx_id: int = -1) -> FaceAnalysis:
    model_dir = Path("models/auraface")
    
    try:
        # 빈 폴더 체크 추가
        if not model_dir.exists() or not any(model_dir.iterdir()):
            print("📥 HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중...")
            snapshot_download(
                "fal/AuraFace-v1", 
                local_dir=str(model_dir),
                local_dir_use_symlinks=False  # Railway/Vercel 호환성
            )
            print("✅ 모델 다운로드 완료")
        else:
            print(f"✅ 기존 모델 사용: {model_dir.absolute()}")
    except Exception as e:
        print(f"⚠️ 경고: 모델 다운로드 중 오류 발생: {e}")
        if not model_dir.exists() or not any(model_dir.iterdir()):
            raise RuntimeError(f"모델을 다운로드할 수 없습니다: {e}")
    
    # 모델 초기화
    model = FaceAnalysis(name="auraface", providers=[...], root=".")
    model.prepare(ctx_id=ctx_id, det_size=(640, 640))
    return model
```

## 📊 배포 프로세스 비교

### Before (기존)
```
Railway 빌드:
1. pip install -r requirements.txt
2. python build_actor_index_insightface.py
   └─> 모델 다운로드 (런타임 시 첫 요청에서)
   └─> 인덱스 생성
3. 서버 시작
   └─> 첫 API 요청 시 모델 다운로드 (느림)
```

### After (개선)
```
Railway 빌드:
1. pip install -r requirements.txt
2. python download_models.py                    ← 추가
   └─> models/auraface/ 폴더에 모델 다운로드
3. python build_actor_index_insightface.py
   └─> 이미 다운로드된 모델 사용
   └─> 인덱스 생성 (302명 배우)
4. 서버 시작
   └─> 즉시 API 요청 처리 가능
```

## 🎯 개선 효과

1. **빌드 시점에 모델 확보**: 배포 완료 시 모델이 이미 준비됨
2. **첫 요청 응답 시간 단축**: 모델 다운로드 대기 시간 제거
3. **안정성 향상**: 런타임 네트워크 문제 영향 최소화
4. **명확한 빌드 로그**: 모델 다운로드 상태를 빌드 로그에서 확인 가능

## 🔍 `build_index_from_cache.py`는 해결책이 아닌 이유

**질문**: "build index from cache"를 실행하면 해결되는 부분이 있는지?

**답변**: ❌ **아니오**

**이유**:
- `build_index_from_cache.py`는 **이미 계산된 임베딩(JSON 캐시)**으로 인덱스 재생성
- **모델을 사용하지 않음** (얼굴 감지/임베딩 계산 없음)
- 따라서 **모델 다운로드를 트리거하지 않음**
- **용도**: 로컬 개발 시 빠른 인덱스 재생성

배포 환경에서는 반드시:
1. **`download_models.py`로 모델 다운로드** (새로 추가)
2. **`build_actor_index_insightface.py`로 인덱스 생성**

## 📝 변경 파일 목록

- ✅ `backend/scripts/download_models.py` (신규 생성)
- ✅ `nixpacks.toml` (빌드 명령 수정)
- ✅ `backend/app/services/embeddings.py` (모델 로딩 로직 개선)

## 🚀 배포 방법

```bash
# 변경사항 커밋 및 푸시
git add .
git commit -m "Add explicit model download step in build phase"
git push origin master

# Railway가 자동으로 재배포 시작 (약 3-5분 소요)
```

## ✅ 검증 방법

Railway 배포 로그에서 다음 메시지 확인:

```
[build] 📥 InsightFace 모델 다운로드 시작
[build] 📥 HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중...
[build] ✅ 모델 다운로드 완료!
[build] 🔮 AuraFace-v1 모델 로딩 중...
[build] ✅ 배우 인덱스 생성 완료: 302명
```

## 📌 참고 사항

- **모델 크기**: 약 150-200MB
- **다운로드 소스**: HuggingFace Hub (`fal/AuraFace-v1`)
- **저장 위치**: `models/auraface/`
- **빌드 시간 증가**: 모델 다운로드로 인해 약 1-2분 추가

---

**업데이트 일시**: 2025-12-01  
**커밋 해시**: e956556  
**이슈**: 배포 환경 모델 다운로드 문제  
**상태**: ✅ 해결 완료
