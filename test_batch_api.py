"""
배치 API 테스트 스크립트
"""
import requests
from pathlib import Path

print("=" * 60)
print("🎭 배치 배우 매칭 테스트")
print("=" * 60)

# 테스트할 이미지들 (dataset에서 몇 개 선택)
test_images = [
    "dataset/강나언/001.jpg",
    "dataset/강미나/001.jpg", 
    "dataset/강민아/001.jpg",
]

# 존재하는 파일만 필터링
files_to_upload = []
for img_path in test_images:
    if Path(img_path).exists():
        files_to_upload.append(img_path)
        print(f"✅ {img_path}")
    else:
        print(f"❌ {img_path} (파일 없음)")

print()
print(f"총 {len(files_to_upload)}개 이미지로 테스트 진행")
print()

# 배치 매칭 요청
files = [("files", (Path(f).name, open(f, "rb"), "image/jpeg")) for f in files_to_upload]
r = requests.post(
    "http://localhost:8000/match-actors-batch?top_k=3&reference_actor=강나언",
    files=files
)

print(f"Status: {r.status_code}")
print()

if r.status_code == 200:
    data = r.json()
    print(f"✅ 배치 매칭 성공!")
    print(f"결과 개수: {len(data['items'])}")
    print()
    
    for idx, item in enumerate(data['items'], 1):
        print("=" * 60)
        print(f"📸 이미지 #{idx}: {files_to_upload[idx-1]}")
        print("=" * 60)
        for i, result in enumerate(item['results'], 1):
            badge = "🎯" if result.get('is_reference') else "  "
            print(f"{badge} {i}. {result['name']}")
            print(f"       유사도: {result['score']:.2%}")
            if result.get('is_reference'):
                print(f"       >>> Target Reference <<<")
        print()
else:
    print(f"❌ 오류: {r.json()}")

print("=" * 60)
print("✅ 배치 테스트 완료")
print("=" * 60)

# 파일 핸들 정리
for _, (_, f, _) in files:
    f.close()
