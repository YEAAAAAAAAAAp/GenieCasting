"""
배포 환경에서 InsightFace 모델을 사전 다운로드하는 스크립트
Railway 빌드 단계에서 실행하여 모델을 미리 다운로드합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def main():
    print("=" * 60)
    print("📥 InsightFace 모델 다운로드 시작")
    print("=" * 60)
    
    try:
        from huggingface_hub import snapshot_download
        
        model_dir = Path("models/auraface")
        
        if model_dir.exists() and any(model_dir.iterdir()):
            print(f"✅ 모델이 이미 존재합니다: {model_dir}")
            print(f"📂 파일 개수: {len(list(model_dir.rglob('*')))}")
            return
        
        print(f"📥 HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중...")
        print(f"📂 대상 경로: {model_dir.absolute()}")
        
        snapshot_download(
            "fal/AuraFace-v1", 
            local_dir=str(model_dir),
            local_dir_use_symlinks=False  # Railway에서는 symlink 비활성화
        )
        
        print("=" * 60)
        print("✅ 모델 다운로드 완료!")
        print(f"📂 저장 위치: {model_dir.absolute()}")
        print(f"📂 파일 개수: {len(list(model_dir.rglob('*')))}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 모델 다운로드 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
