"""
Railway 배포 환경에서 캐시를 압축 해제하고 인덱스를 빌드하는 스크립트
압축된 임베딩 캐시를 사용하여 빠르고 안정적으로 인덱스 생성
"""
import sys
import zipfile
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

print("=" * 60)
print("🚀 Railway 배포: 캐시 압축 해제 + 인덱스 빌드")
print("=" * 60)

# 경로 설정
dataset_dir = project_root / "dataset"
cache_zip = dataset_dir / "embeddings_cache.zip"
embeddings_dir = dataset_dir / "embeddings"

# Step 1: 압축 파일 확인
if not cache_zip.exists():
    print(f"\n❌ 압축 파일을 찾을 수 없습니다: {cache_zip}")
    print("💡 로컬에서 다음 명령으로 생성하세요:")
    print("   Compress-Archive -Path dataset/embeddings -DestinationPath dataset/embeddings_cache.zip")
    sys.exit(1)

print(f"\n✅ 압축 파일 발견: {cache_zip.name}")
print(f"📦 파일 크기: {cache_zip.stat().st_size / 1024 / 1024:.2f} MB")

# Step 2: 압축 해제
if embeddings_dir.exists():
    print(f"\n⚠️  기존 embeddings 폴더 발견, 건너뜀")
else:
    print(f"\n📂 압축 해제 중: {embeddings_dir}")
    try:
        with zipfile.ZipFile(cache_zip, 'r') as zip_ref:
            zip_ref.extractall(dataset_dir)
        print("✅ 압축 해제 완료")
    except Exception as e:
        print(f"❌ 압축 해제 실패: {e}")
        sys.exit(1)

# Step 3: 캐시로 인덱스 생성
print("\n📦 캐시된 임베딩으로 인덱스 생성 중...")
print("⚡ 모델 로딩 불필요 - 빠르고 안정적인 빌드\n")

try:
    from backend.scripts.build_index_from_cache import main as build_from_cache
    build_from_cache()
except Exception as e:
    print(f"\n❌ 인덱스 생성 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Railway 배포 빌드 완료!")
print("📊 캐시 기반 인덱스 생성 (모델은 런타임에 자동 다운로드)")
print("=" * 60)
