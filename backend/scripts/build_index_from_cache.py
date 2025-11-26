"""
캐시된 임베딩 JSON 파일들로부터 인덱스 생성
이미 dataset/embeddings/ 폴더에 캐시가 있으면 빠르게 인덱스 생성
"""
import sys
from pathlib import Path
import json
import numpy as np
from PIL import Image

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.services.search import DATA_DIR, ACTOR_IMAGES_DIR

def load_embeddings_from_cache(dataset_dir: Path):
    """캐시된 임베딩 파일들을 읽어서 배우별 임베딩 리스트 반환"""
    embeddings_dir = dataset_dir / "embeddings"
    
    if not embeddings_dir.exists():
        print(f"❌ 캐시 폴더를 찾을 수 없습니다: {embeddings_dir}")
        return {}
    
    actor_embeddings = {}
    
    # 각 배우 폴더 순회
    for actor_dir in sorted(embeddings_dir.iterdir()):
        if not actor_dir.is_dir():
            continue
        
        actor_name = actor_dir.name
        embeddings = []
        
        # JSON 파일들 읽기
        for json_file in sorted(actor_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    embedding = np.array(data['embedding'], dtype='float32')
                    embeddings.append(embedding)
            except Exception as e:
                print(f"⚠️ {json_file} 로드 실패: {e}")
                continue
        
        if embeddings:
            # 평균 임베딩 계산 후 정규화
            avg_emb = np.mean(embeddings, axis=0)
            avg_emb = avg_emb / (np.linalg.norm(avg_emb) + 1e-12)
            actor_embeddings[actor_name] = avg_emb
            print(f"✅ {actor_name}: {len(embeddings)}개 임베딩 로드")
    
    return actor_embeddings

def main():
    dataset_dir = project_root / "dataset"
    
    if not dataset_dir.exists():
        print(f"❌ dataset 폴더를 찾을 수 없습니다: {dataset_dir}")
        return
    
    print("=" * 60)
    print("📦 캐시된 임베딩으로 인덱스 생성")
    print("=" * 60)
    print(f"📁 데이터셋: {dataset_dir}\n")
    
    # 캐시에서 임베딩 로드
    actor_embeddings = load_embeddings_from_cache(dataset_dir)
    
    if not actor_embeddings:
        print("❌ 로드된 임베딩이 없습니다.")
        return
    
    print(f"\n✅ 총 {len(actor_embeddings)}명의 배우 임베딩 로드 완료\n")
    
    # 인덱스 생성
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ACTOR_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    vectors = []
    meta = []
    
    for actor_name, embedding in sorted(actor_embeddings.items()):
        vectors.append(embedding)
        
        # 대표 이미지 찾기
        actor_image_dir = dataset_dir / actor_name
        rep_rel = None
        
        if actor_image_dir.exists():
            # 첫 번째 이미지 찾기
            for img_file in sorted(actor_image_dir.glob("*.jpg")):
                try:
                    # 대표 이미지 복사
                    actor_folder = ACTOR_IMAGES_DIR / actor_name
                    actor_folder.mkdir(exist_ok=True)
                    target = actor_folder / f"001{img_file.suffix}"
                    
                    if not target.exists():
                        Image.open(img_file).save(target)
                    
                    rep_rel = f"{actor_name}/{target.name}"
                    break
                except Exception as e:
                    print(f"⚠️ {actor_name} 대표 이미지 저장 실패: {e}")
                    continue
        
        meta.append({
            "name": actor_name,
            "image_rel": rep_rel
        })
    
    # 저장
    embeddings_matrix = np.stack(vectors, axis=0)
    embeddings_path = DATA_DIR / "embeddings.npy"
    metadata_path = DATA_DIR / "metadata.json"
    
    np.save(embeddings_path, embeddings_matrix)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("✅ 인덱스 저장 완료!")
    print(f"📊 배우 수: {embeddings_matrix.shape[0]}명")
    print(f"📏 벡터 차원: {embeddings_matrix.shape[1]}")
    print(f"📂 저장 경로:")
    print(f"   - {embeddings_path}")
    print(f"   - {metadata_path}")
    print(f"   - {ACTOR_IMAGES_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()

