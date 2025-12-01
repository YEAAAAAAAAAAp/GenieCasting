"""
배포 환경에서 InsightFace 모델을 사전 다운로드하는 스크립트
Railway 빌드 단계에서 실행하여 모델을 미리 다운로드합니다.
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def main():
    print("=" * 60)
    print("📥 InsightFace 모델 다운로드 시작")
    print("=" * 60)
    
    try:
        # InsightFace 모델 경로 설정
        models_root = Path("/app/models") if os.path.exists("/app") else Path("models")
        models_root.mkdir(parents=True, exist_ok=True)
        
        print(f"📂 모델 저장 경로: {models_root.absolute()}")
        
        # InsightFace 임포트 (자동으로 모델 다운로드)
        from insightface.app import FaceAnalysis
        
        print(f"📥 InsightFace AuraFace-v1 모델 다운로드 중...")
        print(f"⚠️  첫 실행 시 GitHub에서 다운로드 (~100MB)")
        
        # 모델 초기화 및 준비 (다운로드 + 완전 로딩)
        model = FaceAnalysis(
            name='auraface',
            root=str(models_root),
            allowed_modules=['detection', 'recognition'],
            providers=['CPUExecutionProvider']  # 빌드 시 CPU만 사용
        )
        
        print("🔧 모델 준비 중 (완전 초기화)...")
        model.prepare(ctx_id=-1, det_size=(640, 640))  # 완전히 로딩
        
        print("✅ 모델 다운로드 및 준비 완료")
        
        print("=" * 60)
        print("✅ InsightFace 모델 다운로드 성공!")
        print(f"📂 저장 위치: {models_root.absolute()}")
        
        # 다운로드된 파일 확인
        if models_root.exists():
            files = list(models_root.rglob("*"))
            print(f"📂 다운로드된 파일: {len(files)}개")
            for f in files[:5]:  # 첫 5개만 표시
                print(f"  - {f.relative_to(models_root)}")
            if len(files) > 5:
                print(f"  ... 및 {len(files) - 5}개 더")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 모델 다운로드 실패: {e}")
        print("⚠️  런타임에 재시도됩니다.")
        import traceback
        traceback.print_exc()
        # 빌드 실패하지 않도록 exit(0)
        print("\n⚙️  빌드는 계속 진행합니다 (런타임 다운로드 폴백)")
        sys.exit(0)

if __name__ == "__main__":
    main()
