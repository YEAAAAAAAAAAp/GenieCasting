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
    print("🔮 AuraFace-v1 모델 로딩 중...")
    
    # HuggingFace Hub에서 모델 다운로드
    try:
        model_dir = Path("models/auraface")
        if not model_dir.exists():
            print("📥 HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중...")
            snapshot_download("fal/AuraFace-v1", local_dir=str(model_dir))
            print("✅ 모델 다운로드 완료")
    except Exception as e:
        print(f"⚠️ 경고: 모델 다운로드 중 오류 발생: {e}")
        print("기존 다운로드된 모델을 사용합니다.")
    
    # 모델 초기화
    model = FaceAnalysis(
        name="auraface",
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        root=".",
    )
    model.prepare(ctx_id=ctx_id, det_size=(640, 640))
    
    print("✅ AuraFace-v1 모델 로딩 완료")
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
    # 캐시에서 로드 시도
    if use_cache and image_path:
        cache_path = _get_cache_path(image_path)
        cached_embedding = _load_embedding_from_cache(cache_path)
        if cached_embedding is not None:
            return cached_embedding
    
    # 캐시가 없거나 사용하지 않는 경우, 임베딩 계산
    try:
        model = get_insightface_model(ctx_id=ctx_id)
        cv_image = _load_image(img_bytes)
        
        # 얼굴 감지 및 임베딩 추출
        faces = model.get(cv_image)
        
        if not faces or len(faces) == 0:
            return None
        
        # 첫 번째 얼굴의 정규화된 임베딩 반환 (normed_embedding)
        embedding = faces[0].normed_embedding.astype("float32")
        
        # 캐시에 저장
        if use_cache and image_path:
            cache_path = _get_cache_path(image_path)
            _save_embedding_to_cache(cache_path, embedding)
        
        return embedding
        
    except Exception as e:
        print(f"❌ AuraFace-v1 임베딩 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None
