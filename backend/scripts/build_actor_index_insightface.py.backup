"""
InsightFace AuraFace-v1 기반 배우 인덱스 생성 스크립트

기존 CLIP 버전과 동일한 인터페이스를 유지하면서 InsightFace 모델을 사용합니다.

두 가지 데이터셋 구조를 지원합니다:
1) 폴더 기반 (권장):
   dataset_dir/
     배우이름A/*.jpg
     배우이름B/*.png
   => 각 폴더의 이미지 임베딩 평균을 배우 대표 벡터로 저장

2) CSV 기반:
   --csv file.csv (columns: name,image_path)
   => 같은 이름을 가진 이미지들을 그룹핑하여 평균

출력: backend/app/data/
  - embeddings.npy (shape: [N_actors, 512])
  - metadata.json (list[{name, image_rel}])
  - actors/ (대표 이미지 복사본)
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from backend.app.services.embeddings import image_embedding
from backend.app.services.search import DATA_DIR, ACTOR_IMAGES_DIR


def iter_folder(dataset_dir: Path) -> Dict[str, List[Path]]:
    """폴더 구조에서 배우별 이미지 경로 매핑 생성"""
    mapping: Dict[str, List[Path]] = defaultdict(list)
    # embeddings 폴더는 배우로 인식하지 않음
    for actor_dir in sorted([p for p in dataset_dir.iterdir() if p.is_dir() and p.name != "embeddings"]):
        name = actor_dir.name
        for img in actor_dir.rglob("*"):
            if img.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                mapping[name].append(img)
    return mapping


def iter_csv(csv_path: Path) -> Dict[str, List[Path]]:
    """CSV 파일에서 배우별 이미지 경로 매핑 생성"""
    mapping: Dict[str, List[Path]] = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            img_path = Path(row["image_path"]).expanduser().resolve()
            if img_path.exists():
                mapping[name].append(img_path)
    return mapping


def compute_actor_vectors(groups: Dict[str, List[Path]], clusters_per_actor: int = 1) -> Tuple[np.ndarray, List[Dict]]:
    """
    배우별 이미지들을 InsightFace 임베딩으로 변환하고 평균 벡터 생성
    
    Args:
        groups: 배우 이름 -> 이미지 경로 리스트 매핑
        clusters_per_actor: 배우당 클러스터 개수 (기본 1)
        
    Returns:
        (embeddings_matrix, metadata_list)
    """
    ACTOR_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    vectors = []
    meta: List[Dict] = []
    
    total_actors = len(groups)
    processed = 0
    
    print(f"\n🔮 InsightFace로 배우 인덱스 생성 시작 (총 {total_actors}명)")
    print("=" * 60)
    
    for name, paths in sorted(groups.items()):
        if not paths:
            continue
            
        processed += 1
        print(f"\n[{processed}/{total_actors}] 처리 중: {name} ({len(paths)}장)")
        
        embs = []
        rep_rel = None
        face_detected_count = 0
        
        for i, p in enumerate(paths[:20]):  # 최대 20장까지 샘플링
            try:
                with open(p, "rb") as f:
                    emb = image_embedding(f.read(), image_path=str(p), use_cache=True)
                
                if emb is None:
                    print(f"  ⚠️  {p.name}: 얼굴 감지 실패")
                    continue
                
                embs.append(emb)
                face_detected_count += 1
                
                # 첫 번째 성공한 이미지를 대표 이미지로 저장
                if rep_rel is None:
                    # 배우 이름으로 폴더 생성
                    actor_folder = ACTOR_IMAGES_DIR / name
                    actor_folder.mkdir(exist_ok=True)
                    
                    # 001.jpg 형식으로 저장
                    target = actor_folder / f"001{p.suffix.lower()}"
                    if not target.exists():
                        try:
                            Image.open(p).save(target)
                            print(f"  ✅ 대표 이미지 저장: {target.relative_to(ACTOR_IMAGES_DIR)}")
                        except Exception as e:
                            print(f"  ⚠️  이미지 복사 실패: {e}")
                            continue
                    
                    if target.exists():
                        # 상대 경로 저장 (예: "송강호/001.jpg")
                        rep_rel = f"{name}/{target.name}"
                        
            except Exception as e:
                print(f"  ❌ {p.name}: {e}")
                continue
        
        if not embs:
            print(f"  ⚠️  {name}: 얼굴이 감지된 이미지가 없어 제외됩니다")
            continue
        
        print(f"  ✅ {face_detected_count}/{len(paths[:20])}장에서 얼굴 감지 성공")
        
        # 임베딩 행렬 생성
        X = np.stack(embs, axis=0)
        
        # 클러스터링 또는 평균 벡터 생성
        if clusters_per_actor > 1 and len(embs) >= clusters_per_actor:
            try:
                from sklearn.cluster import KMeans
                km = KMeans(n_clusters=clusters_per_actor, n_init=10, random_state=42)
                labels = km.fit_predict(X)
                
                for c in range(clusters_per_actor):
                    members = X[labels == c]
                    if members.size == 0:
                        continue
                    centroid = members.mean(axis=0)
                    centroid = centroid / (np.linalg.norm(centroid) + 1e-12)
                    vectors.append(centroid.astype("float32"))
                    meta.append({"name": name, "image_rel": rep_rel, "cluster": c})
                    
                print(f"  📊 {clusters_per_actor}개 클러스터 생성")
            except Exception as e:
                print(f"  ⚠️  클러스터링 실패, 평균 벡터 사용: {e}")
                # 클러스터링 실패 시 평균 벡터로 폴백
                mean_vec = np.mean(X, axis=0)
                mean_vec = mean_vec / (np.linalg.norm(mean_vec) + 1e-12)
                vectors.append(mean_vec.astype("float32"))
                meta.append({"name": name, "image_rel": rep_rel})
        else:
            # 단순 평균 벡터
            mean_vec = np.mean(X, axis=0)
            mean_vec = mean_vec / (np.linalg.norm(mean_vec) + 1e-12)
            vectors.append(mean_vec.astype("float32"))
            meta.append({"name": name, "image_rel": rep_rel})
            print(f"  📊 평균 벡터 생성 완료")
    
    print("\n" + "=" * 60)
    print(f"✅ 배우 인덱스 생성 완료: {len(vectors)}명")
    
    if not vectors:
        raise ValueError("유효한 배우 벡터가 생성되지 않았습니다. 이미지에 얼굴이 포함되어 있는지 확인하세요.")
    
    return np.stack(vectors, axis=0), meta


def main():
    parser = argparse.ArgumentParser(description="InsightFace 기반 배우 인덱스 생성")
    parser.add_argument("--dataset-dir", type=str, help="배우 이미지 루트 폴더")
    parser.add_argument("--csv", type=str, help="'name,image_path' CSV 파일 경로")
    parser.add_argument("--clusters-per-actor", type=int, default=1, help="배우별 클러스터 개수 (>=1)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 데이터셋 로드
    groups: Dict[str, List[Path]]
    if args.dataset_dir:
        print(f"📁 폴더 기반 데이터셋 로드: {args.dataset_dir}")
        groups = iter_folder(Path(args.dataset_dir))
    elif args.csv:
        print(f"📄 CSV 기반 데이터셋 로드: {args.csv}")
        groups = iter_csv(Path(args.csv))
    else:
        raise SystemExit("❌ --dataset-dir 또는 --csv 중 하나는 필수입니다")

    if not groups:
        raise SystemExit("❌ 데이터셋에서 이미지를 찾지 못했습니다")

    print(f"✅ {len(groups)}명의 배우 데이터 로드 완료")

    # InsightFace로 임베딩 생성
    emb, meta = compute_actor_vectors(groups, clusters_per_actor=max(1, int(args.clusters_per_actor)))
    
    # 저장
    embeddings_path = DATA_DIR / "embeddings.npy"
    metadata_path = DATA_DIR / "metadata.json"
    
    np.save(embeddings_path, emb)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✅ 인덱스 저장 완료!")
    print(f"📊 배우 수: {emb.shape[0]}명")
    print(f"📏 벡터 차원: {emb.shape[1]}")
    print(f"📂 저장 경로:")
    print(f"   - {embeddings_path}")
    print(f"   - {metadata_path}")
    print(f"   - {ACTOR_IMAGES_DIR}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
