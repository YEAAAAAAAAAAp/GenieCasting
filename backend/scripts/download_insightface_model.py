"""
Railway 빌드 시 InsightFace AuraFace-v1 모델 사전 다운로드
"""
from pathlib import Path
from huggingface_hub import snapshot_download

def download_model():
    """HuggingFace Hub에서 AuraFace-v1 모델 다운로드"""
    model_dir = Path("models/auraface")
    
    print("=" * 60)
    print("🔮 InsightFace AuraFace-v1 모델 다운로드 시작")
    print("=" * 60)
    
    try:
        # 이미 다운로드되어 있는지 확인
        if model_dir.exists() and any(model_dir.iterdir()):
            print(f"✅ 모델이 이미 존재합니다: {model_dir.absolute()}")
            # 파일 목록 출력
            for file in model_dir.iterdir():
                print(f"  - {file.name}")
            return
        
        # 모델 디렉토리 생성
        model_dir.mkdir(parents=True, exist_ok=True)
        
        print("📥 HuggingFace Hub에서 다운로드 중...")
        print(f"📂 저장 경로: {model_dir.absolute()}")
        
        # HuggingFace Hub에서 모델 다운로드
        snapshot_download(
            "fal/AuraFace-v1",
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,  # Railway/Vercel 호환성
            resume_download=True
        )
        
        print("\n✅ 모델 다운로드 완료!")
        print("\n📁 다운로드된 파일:")
        for file in model_dir.rglob("*"):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  - {file.relative_to(model_dir)}: {size_mb:.2f} MB")
        
        print("\n" + "=" * 60)
        print("🎉 모델 준비 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    download_model()
