"""
Railway 배포 환경에서 캐시를 생성하고 인덱스를 빌드하는 통합 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

print("=" * 60)
print("🚀 Railway 배포: 임베딩 캐시 생성 + 인덱스 빌드")
print("=" * 60)

# Step 1: 캐시가 있는지 확인
dataset_dir = project_root / "dataset"
embeddings_cache_dir = dataset_dir / "embeddings"

cache_exists = embeddings_cache_dir.exists()
actor_count = 0

if cache_exists:
    actor_dirs = [d for d in embeddings_cache_dir.iterdir() if d.is_dir()]
    actor_count = len(actor_dirs)
    print(f"\n✅ 기존 캐시 발견: {actor_count}명의 배우")

if cache_exists and actor_count > 0:
    # 캐시가 있으면 build_index_from_cache 사용
    print("\n📦 캐시된 임베딩으로 인덱스 생성 중...")
    from backend.scripts.build_index_from_cache import main as build_from_cache
    build_from_cache()
else:
    # 캐시가 없으면 build_actor_index_insightface 사용
    print("\n🔮 InsightFace로 임베딩 생성 및 인덱스 빌드 중...")
    print("⚠️  경고: 이 방식은 시간이 오래 걸리고 모델 로딩 문제가 있을 수 있습니다.\n")
    
    import argparse
    from backend.scripts.build_actor_index_insightface import main as build_with_model
    
    # 가짜 args 생성
    sys.argv = [
        'build_actor_index_insightface.py',
        '--dataset-dir', str(dataset_dir)
    ]
    
    try:
        build_with_model()
    except Exception as e:
        print(f"\n❌ 모델 기반 빌드 실패: {e}")
        print("💡 해결책: 로컬에서 캐시를 생성하고 Git에 커밋하세요.")
        sys.exit(1)

print("\n" + "=" * 60)
print("✅ 배포 빌드 완료!")
print("=" * 60)
