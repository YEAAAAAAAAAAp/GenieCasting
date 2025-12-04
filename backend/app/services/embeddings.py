"""
InsightFace AuraFace-v1 기반 얼굴 임베딩 서비스 (Image_RAG 의존성 제거)
"""
from functools import lru_cache
from io import BytesIO
from typing import Optional, Union
from pathlib import Path
import json

import numpy as np
from PIL import Image
import cv2

try:
    from insightface.app import FaceAnalysis
except ImportError:
    print("필요한 패키지를 설치해주세요: pip install insightface")
    raise

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("필요한 패키지를 설치해주세요: pip install huggingface_hub")
    raise


@lru_cache(maxsize=1)
def get_insightface_model(ctx_id: int = -1) -> FaceAnalysis:
    """
    InsightFace AuraFace-v1 모델 싱글톤
    최초 호출 시 모델을 로드하고 캐시합니다.
    
    Args:
        ctx_id: 디바이스 ID (0: GPU, -1: CPU)
    """
    import sys
    print("🔮 AuraFace-v1 모델 로딩 중...")
    print(f"[DEBUG] Python version: {sys.version}")
    print(f"[DEBUG] Available memory check...")
    
    # HuggingFace Hub에서 모델 다운로드
    model_dir = Path("models/auraface")
    
    # 모델 파일 검증 함수
    def validate_onnx_files(directory: Path) -> tuple[bool, list[Path]]:
        """ONNX 파일이 손상되지 않았는지 검증"""
        if not directory.exists():
            return False, []
        
        onnx_files = list(directory.glob("*.onnx"))
        if len(onnx_files) < 3:
            return False, onnx_files
        
        # 파일 크기 검증 (손상된 파일은 0 바이트이거나 매우 작음)
        valid_files = []
        for file in onnx_files:
            size = file.stat().st_size
            if size > 1024 * 100:  # 최소 100KB 이상
                valid_files.append(file)
        
        return len(valid_files) >= 3, valid_files
    
    # 모델 파일 확인 및 다운로드 (필요시)
    is_valid, model_files = validate_onnx_files(model_dir)
    
    if not is_valid:
        print(f"📥 모델 파일 다운로드 필요 (현재: {len(model_files)}개 유효 ONNX 파일)")
        print("⏳ HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중... (약 5-10분 소요)")
        print("⚠️ 첫 배포 시에만 실행되며, 이후에는 캐시된 모델을 사용합니다.")
        
        try:
            # 기존 불완전한 파일 삭제
            if model_dir.exists():
                import shutil
                print("🗑️ 손상된 기존 모델 파일 삭제 중...")
                shutil.rmtree(model_dir, ignore_errors=True)
            
            # 재다운로드
            model_dir.parent.mkdir(parents=True, exist_ok=True)
            snapshot_download(
                "fal/AuraFace-v1", 
                local_dir=str(model_dir),
                resume_download=True  # 중단된 다운로드 재개
            )
            print("✅ 모델 다운로드 완료")
            
            # 다운로드 성공 확인
            is_valid, model_files = validate_onnx_files(model_dir)
            if not is_valid:
                raise RuntimeError(f"모델 다운로드 후에도 파일이 불완전합니다: {len(model_files)}개")
                
        except Exception as e:
            raise RuntimeError(
                f"모델 다운로드 실패: {e}\n"
                "해결 방법:\n"
                "1. Railway에서 첫 배포 시 타임아웃이 발생할 수 있습니다.\n"
                "2. 재배포하면 Railway가 이전 빌드를 캐시하여 성공합니다.\n"
                "3. 또는 Git LFS를 사용하여 대용량 모델 파일을 관리하세요."
            )
    
    print(f"✅ 모델 파일 검증 완료: {len(model_files)}개 유효 ONNX 파일")
    
    # 메모리 정리 (모델 로딩 전)
    import gc
    gc.collect()
    
    # 모델 초기화 (CPU만 사용)
    print("📦 모델 초기화 시작...")
    model = FaceAnalysis(
        name="auraface",
        providers=["CPUExecutionProvider"],  # CPU만 사용
        root=".",
    )
    
    # Railway 업그레이드로 640x640 고해상도 사용 가능
    print("⚙️ 모델 준비 중 (고해상도 모드)...")
    model.prepare(ctx_id=ctx_id, det_size=(640, 640))
    
    # 메모리 정리
    gc.collect()
    
    print("✅ AuraFace-v1 모델 로딩 완료 (고해상도)")
    return model


def _load_image(img_bytes: bytes) -> np.ndarray:
    """이미지 바이트를 OpenCV 형식(BGR)으로 변환"""
    pil_image = Image.open(BytesIO(img_bytes))
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    
    # PIL RGB -> OpenCV BGR
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return cv_image


def _get_cache_path(image_path: Union[str, Path]) -> Path:
    """
    이미지 파일 경로를 기반으로 캐시 파일 경로 생성
    
    Args:
        image_path: 이미지 파일 경로 (예: dataset/강나언/001.jpg) 또는 파일명만 (예: image2.jpg)
        
    Returns:
        캐시 파일 경로 (예: dataset/embeddings/강나언/001.json)
    """
    image_path = Path(image_path)
    
    # 파일명만 있는 경우 (업로드된 파일 등)
    if len(image_path.parts) == 1:
        # uploads/embeddings/image2.json 형식으로 저장
        cache_dir = Path("uploads") / "embeddings"
        cache_filename = image_path.stem + ".json"
        return cache_dir / cache_filename
    
    # dataset/강나언/001.jpg -> dataset/embeddings/강나언/001.json
    if "dataset" in image_path.parts:
        # dataset 폴더 찾기
        parts = list(image_path.parts)
        dataset_idx = parts.index("dataset")
        # dataset 폴더 경로
        dataset_path = Path(*parts[:dataset_idx + 1])
        # dataset 이후 경로 (강나언/001.jpg)
        relative_parts = parts[dataset_idx + 1:]
        
        if len(relative_parts) >= 2:
            # 배우 이름과 파일명
            actor_name = relative_parts[0]
            filename = relative_parts[-1]
            # 확장자 제거하고 .json 추가
            cache_filename = Path(filename).stem + ".json"
            
            # dataset/embeddings/강나언/001.json 경로 생성
            cache_path = dataset_path / "embeddings" / actor_name / cache_filename
            return cache_path
    
    # dataset이 아닌 경우, 이미지 파일과 같은 디렉토리에 embeddings 폴더 생성
    # 예: image2.jpg -> embeddings/image2.json
    cache_dir = image_path.parent / "embeddings"
    cache_filename = image_path.stem + ".json"
    return cache_dir / cache_filename


def _load_embedding_from_cache(cache_path: Path) -> Optional[np.ndarray]:
    """캐시 파일에서 임베딩 로드"""
    try:
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        embedding = np.array(data['embedding'], dtype='float32')
        return embedding
    except Exception as e:
        print(f"⚠️ 캐시 로드 실패 ({cache_path}): {e}")
        return None


def _save_embedding_to_cache(cache_path: Path, embedding: np.ndarray) -> None:
    """임베딩을 캐시 파일에 저장"""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'embedding': embedding.tolist(),
            'shape': list(embedding.shape),
            'dtype': str(embedding.dtype)
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 캐시 저장 실패 ({cache_path}): {e}")


def image_embedding(
    img_bytes: bytes, 
    ctx_id: int = -1,
    image_path: Optional[Union[str, Path]] = None,
    use_cache: bool = True
) -> Optional[np.ndarray]:
    """
    이미지를 512차원 얼굴 임베딩 벡터로 변환 (InsightFace AuraFace-v1)
    
    Args:
        img_bytes: 이미지 바이트 데이터
        ctx_id: 디바이스 ID (0: GPU, -1: CPU)
        image_path: 이미지 파일 경로 (캐싱용, 선택사항)
        use_cache: 캐시 사용 여부 (기본값: True)
        
    Returns:
        512차원 numpy 배열 (float32, L2-normalized) 또는 None (얼굴이 없는 경우)
    """
    print(f"[DEBUG] image_embedding called - image_path: {image_path}, use_cache: {use_cache}")
    
    # 캐시에서 로드 시도
    if use_cache and image_path:
        cache_path = _get_cache_path(image_path)
        cached_embedding = _load_embedding_from_cache(cache_path)
        if cached_embedding is not None:
            print(f"[DEBUG] Cache hit: {cache_path}")
            return cached_embedding
        else:
            print(f"[DEBUG] Cache miss: {cache_path}")
    
    # 캐시가 없거나 사용하지 않는 경우, 임베딩 계산
    try:
        print("[DEBUG] Loading InsightFace model...")
        model = get_insightface_model(ctx_id=ctx_id)
        print("[DEBUG] Model loaded, processing image...")
        
        cv_image = _load_image(img_bytes)
        print(f"[DEBUG] Image shape: {cv_image.shape}")
        
        # 얼굴 감지 및 임베딩 추출
        faces = model.get(cv_image)
        print(f"[DEBUG] Detected faces: {len(faces) if faces else 0}")
        
        if not faces or len(faces) == 0:
            print("[DEBUG] No faces detected")
            return None
        
        # 첫 번째 얼굴의 정규화된 임베딩 반환 (normed_embedding)
        embedding = faces[0].normed_embedding.astype("float32")
        print(f"[DEBUG] Embedding shape: {embedding.shape}")
        
        # 캐시에 저장
        if use_cache and image_path:
            cache_path = _get_cache_path(image_path)
            _save_embedding_to_cache(cache_path, embedding)
            print(f"[DEBUG] Saved to cache: {cache_path}")
        
        return embedding
        
    except Exception as e:
        print(f"❌ AuraFace-v1 임베딩 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None
