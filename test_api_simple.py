"""
간단한 API 테스트 스크립트
"""
import requests

# 1. Health check
print("=" * 60)
print("🔍 Health Check")
print("=" * 60)
r = requests.get("http://localhost:8000/health")
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")
print()

# 2. Match actors with test image
print("=" * 60)
print("🎭 배우 매칭 테스트 (image2.jpg)")
print("=" * 60)
with open("image2.jpg", "rb") as f:
    files = {"file": ("image2.jpg", f, "image/jpeg")}
    r = requests.post("http://localhost:8000/match-actors?top_k=3", files=files)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"\n✅ 매칭 성공!")
        print(f"결과 개수: {len(data['results'])}")
        for i, result in enumerate(data['results'], 1):
            print(f"\n{i}. {result['name']}")
            print(f"   유사도: {result['score']:.2%}")
            if 'image_url' in result:
                print(f"   이미지: {result['image_url']}")
    else:
        print(f"❌ 오류: {r.json()}")
print()

print("=" * 60)
print("✅ 테스트 완료")
print("=" * 60)
