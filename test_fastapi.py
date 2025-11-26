"""
FastAPI 엔드포인트 테스트 스크립트
캐싱 기능 포함
"""
import sys
from pathlib import Path
import requests
import time

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_health():
    """Health check 엔드포인트 테스트"""
    print("=" * 80)
    print("🔍 Health Check 테스트")
    print("=" * 80)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Health check 성공: {response.json()}")
            return True
        else:
            print(f"❌ Health check 실패: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 백엔드 서버에 연결할 수 없습니다.")
        print("   서버를 먼저 시작하세요:")
        print("   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def test_match_actors_single():
    """단일 이미지 매칭 테스트 (캐싱 포함)"""
    print("\n" + "=" * 80)
    print("🎭 단일 이미지 매칭 테스트 (캐싱 포함)")
    print("=" * 80)
    
    test_image = project_root / "image2.jpg"
    if not test_image.exists():
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {test_image}")
        return False
    
    try:
        # 첫 번째 요청 (캐시 없음 - 계산 필요)
        print(f"\n📤 첫 번째 요청 (캐시 없음)...")
        start_time = time.time()
        with open(test_image, "rb") as f:
            files = {"file": ("image2.jpg", f, "image/jpeg")}
            response = requests.post(
                "http://localhost:8000/match-actors?top_k=3", 
                files=files,
                timeout=30
            )
        first_request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 첫 번째 요청 성공 (소요 시간: {first_request_time:.2f}초)")
            print(f"   결과 개수: {len(data['results'])}")
            for i, result in enumerate(data['results'], 1):
                print(f"   {i}. {result['name']:15s} - 유사도: {result['score']:.2%}")
        else:
            print(f"❌ 첫 번째 요청 실패: {response.status_code}")
            print(f"   응답: {response.json()}")
            return False
        
        # 두 번째 요청 (캐시 있음 - 빠른 응답)
        print(f"\n📤 두 번째 요청 (캐시 있음)...")
        start_time = time.time()
        with open(test_image, "rb") as f:
            files = {"file": ("image2.jpg", f, "image/jpeg")}
            response = requests.post(
                "http://localhost:8000/match-actors?top_k=3", 
                files=files,
                timeout=30
            )
        second_request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 두 번째 요청 성공 (소요 시간: {second_request_time:.2f}초)")
            print(f"   결과 개수: {len(data['results'])}")
            for i, result in enumerate(data['results'], 1):
                print(f"   {i}. {result['name']:15s} - 유사도: {result['score']:.2%}")
            
            # 캐싱 효과 확인
            if second_request_time < first_request_time:
                speedup = first_request_time / second_request_time
                print(f"\n🚀 캐싱 효과: {speedup:.2f}x 빠름")
            else:
                print(f"\n⚠️  캐싱 효과가 없거나 미미함")
        else:
            print(f"❌ 두 번째 요청 실패: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_match_actors_batch():
    """배치 이미지 매칭 테스트"""
    print("\n" + "=" * 80)
    print("🎬 배치 이미지 매칭 테스트")
    print("=" * 80)
    
    dataset_dir = project_root / "dataset"
    if not dataset_dir.exists():
        print(f"❌ 데이터셋 폴더를 찾을 수 없습니다: {dataset_dir}")
        return False
    
    # 각 배우 폴더에서 첫 번째 이미지 가져오기
    test_images = []
    for actor_dir in sorted([d for d in dataset_dir.iterdir() if d.is_dir() and d.name != "embeddings"]):
        images = list(actor_dir.glob("*.jpg"))
        if images:
            test_images.append(images[0])
    
    if not test_images:
        print("❌ 테스트할 이미지를 찾을 수 없습니다.")
        return False
    
    print(f"📸 테스트 이미지: {len(test_images)}개")
    
    try:
        files = []
        for img_path in test_images[:3]:  # 최대 3개만 테스트
            files.append(("files", (img_path.name, open(img_path, "rb"), "image/jpeg")))
        
        response = requests.post(
            "http://localhost:8000/match-actors-batch?top_k=3",
            files=files,
            timeout=60
        )
        
        # 파일 닫기
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 배치 매칭 성공")
            print(f"   처리된 이미지: {len(data['items'])}개")
            
            for item in data['items']:
                if 'error' in item:
                    print(f"   ❌ {item['filename']}: {item['error']}")
                else:
                    print(f"   ✅ {item['filename']}: {len(item['results'])}개 결과")
                    for i, result in enumerate(item['results'][:3], 1):
                        print(f"      {i}. {result['name']:15s} - {result['score']:.2%}")
            return True
        else:
            print(f"❌ 배치 매칭 실패: {response.status_code}")
            print(f"   응답: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 80)
    print("🚀 FastAPI 엔드포인트 테스트 (캐싱 포함)")
    print("=" * 80)
    
    results = []
    
    # Health check
    results.append(("Health Check", test_health()))
    
    if results[0][1]:  # Health check 성공 시에만 계속
        results.append(("단일 이미지 매칭 (캐싱)", test_match_actors_single()))
        results.append(("배치 이미지 매칭", test_match_actors_batch()))
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    for name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())

