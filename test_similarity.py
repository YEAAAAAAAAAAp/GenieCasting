"""
배우 유사도 테스트 스크립트
image2.jpg (지원 배우)와 dataset의 유명 배우들 간 유사도 분석
"""
import sys
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.services.embeddings import image_embedding

def load_image_bytes(image_path: Path) -> bytes:
    """이미지 파일을 바이트로 로드"""
    with open(image_path, 'rb') as f:
        return f.read()

def get_actor_representative_embedding(actor_dir: Path) -> tuple[str, np.ndarray | None]:
    """배우 폴더의 이미지들을 평균내어 대표 임베딩 생성"""
    actor_name = actor_dir.name
    embeddings = []
    
    for img_path in actor_dir.glob("*.jpg"):
        try:
            img_bytes = load_image_bytes(img_path)
            emb = image_embedding(img_bytes, image_path=str(img_path), use_cache=True)
            if emb is not None:
                embeddings.append(emb)
        except Exception as e:
            print(f"  ⚠️ {img_path.name} 처리 실패: {e}")
    
    if embeddings:
        # 평균 임베딩 계산 후 정규화
        avg_emb = np.mean(embeddings, axis=0)
        avg_emb = avg_emb / np.linalg.norm(avg_emb)
        return actor_name, avg_emb
    else:
        return actor_name, None

def main():
    print("=" * 80)
    print("🎬 Genie Match - 배우 유사도 테스트")
    print("=" * 80)
    
    # 1. 지원 배우 이미지 로드
    query_image_path = project_root / "image2.jpg"
    print(f"\n📸 지원 배우 이미지: {query_image_path}")
    
    if not query_image_path.exists():
        print(f"❌ 이미지를 찾을 수 없습니다: {query_image_path}")
        return
    
    query_bytes = load_image_bytes(query_image_path)
    query_embedding = image_embedding(query_bytes, image_path=str(query_image_path), use_cache=True)
    
    if query_embedding is None:
        print("❌ 지원 배우 이미지에서 얼굴을 감지할 수 없습니다.")
        return
    
    print(f"✅ 지원 배우 임베딩 생성 완료 (차원: {query_embedding.shape})")
    
    # 2. 레퍼런스 배우들 임베딩 생성
    dataset_dir = project_root / "dataset"
    print(f"\n🎭 레퍼런스 배우 데이터셋: {dataset_dir}")
    
    if not dataset_dir.exists():
        print(f"❌ 데이터셋 폴더를 찾을 수 없습니다: {dataset_dir}")
        return
    
    # embeddings 폴더는 배우로 인식하지 않음
    actor_dirs = sorted([d for d in dataset_dir.iterdir() if d.is_dir() and d.name != "embeddings"])
    print(f"📊 총 {len(actor_dirs)}명의 배우 발견\n")
    
    # 각 배우의 대표 임베딩 생성
    print("🔮 배우별 임베딩 생성 중...\n")
    actor_embeddings = []
    
    for actor_dir in actor_dirs:
        print(f"처리 중: {actor_dir.name}")
        actor_name, actor_emb = get_actor_representative_embedding(actor_dir)
        
        if actor_emb is not None:
            actor_embeddings.append({
                'name': actor_name,
                'embedding': actor_emb
            })
            print(f"  ✅ {actor_name} 임베딩 완료\n")
        else:
            print(f"  ❌ {actor_name} 얼굴 감지 실패\n")
    
    if not actor_embeddings:
        print("❌ 처리된 배우가 없습니다.")
        return
    
    print(f"✅ 총 {len(actor_embeddings)}명의 배우 임베딩 완료\n")
    
    # 3. 유사도 계산
    print("=" * 80)
    print("📊 유사도 분석 결과")
    print("=" * 80)
    
    similarities = []
    for actor in actor_embeddings:
        # 코사인 유사도 계산
        sim = cosine_similarity(
            query_embedding.reshape(1, -1),
            actor['embedding'].reshape(1, -1)
        )[0][0]
        
        similarities.append({
            'name': actor['name'],
            'score': sim
        })
    
    # 유사도 순으로 정렬
    similarities.sort(key=lambda x: x['score'], reverse=True)
    
    # 결과 출력
    print(f"\n🏆 Top 10 유사 배우:\n")
    for i, result in enumerate(similarities[:10], 1):
        score_percent = result['score'] * 100
        bar_length = int(score_percent / 2)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        
        print(f"{i:2d}. {result['name']:15s} │ {bar} │ {score_percent:.2f}%")
    
    # 전체 결과 요약
    print(f"\n" + "=" * 80)
    print(f"📈 통계 정보:")
    print(f"   - 최고 유사도: {similarities[0]['name']} ({similarities[0]['score']*100:.2f}%)")
    print(f"   - 평균 유사도: {np.mean([s['score'] for s in similarities])*100:.2f}%")
    print(f"   - 최저 유사도: {similarities[-1]['name']} ({similarities[-1]['score']*100:.2f}%)")
    print("=" * 80)
    
    # 전체 결과 저장
    print(f"\n💾 전체 결과를 test_results.txt에 저장 중...")
    with open(project_root / "test_results.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("Genie Match - 배우 유사도 테스트 결과\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"지원 배우 이미지: image2.jpg\n\n")
        f.write("전체 유사도 순위:\n\n")
        
        for i, result in enumerate(similarities, 1):
            f.write(f"{i:3d}. {result['name']:20s} {result['score']*100:6.2f}%\n")
    
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    main()
