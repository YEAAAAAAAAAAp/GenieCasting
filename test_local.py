"""
로컬 테스트 스크립트
백엔드와 프론트엔드 통합 테스트
"""
import subprocess
import time
import requests
import sys
from pathlib import Path

def test_backend():
    """백엔드 서버 테스트"""
    print("=" * 60)
    print("🔍 백엔드 서버 테스트")
    print("=" * 60)
    
    # Health check
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check 성공:", response.json())
            return True
        else:
            print(f"❌ Health check 실패: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 백엔드 서버에 연결할 수 없습니다.")
        print("   서버를 먼저 시작하세요:")
        print("   .\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def test_api_docs():
    """API 문서 접근 테스트"""
    print("\n" + "=" * 60)
    print("📚 API 문서 테스트")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API 문서 접근 성공")
            print("   URL: http://localhost:8000/docs")
            return True
        else:
            print(f"❌ API 문서 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def test_match_actors_endpoint():
    """배우 매칭 엔드포인트 테스트 (인덱스 없이)"""
    print("\n" + "=" * 60)
    print("🎭 배우 매칭 엔드포인트 테스트")
    print("=" * 60)
    
    try:
        # 더미 이미지 파일 생성
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(
            "http://localhost:8000/match-actors?top_k=3",
            files=files,
            timeout=10
        )
        
        if response.status_code == 503:
            print("⚠️  배우 인덱스가 생성되지 않았습니다 (예상된 결과)")
            print("   인덱스 생성 명령:")
            print("   python backend\\scripts\\build_actor_index_insightface.py --dataset-dir <경로>")
            return True
        elif response.status_code == 400:
            print("⚠️  얼굴 감지 실패 (예상된 결과 - 더미 이미지)")
            return True
        elif response.status_code == 200:
            print("✅ 배우 매칭 성공:", response.json())
            return True
        else:
            print(f"❌ 예상치 못한 응답: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def main():
    print("\n" + "="  * 60)
    print("🚀 Genie Match 로컬 테스트")
    print("=" * 60)
    
    results = []
    
    # 백엔드 테스트
    results.append(("Backend Health", test_backend()))
    
    if results[0][1]:  # Health check 성공 시에만 계속
        results.append(("API Docs", test_api_docs()))
        results.append(("Match Actors Endpoint", test_match_actors_endpoint()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
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
