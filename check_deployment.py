"""
Railway 배포 최종 검증 스크립트
모든 필수 파일과 설정을 확인합니다
"""
import os
import json
from pathlib import Path

def check_deployment_readiness():
    """배포 준비 상태 검증"""
    errors = []
    warnings = []
    
    print("=" * 60)
    print("🔍 Railway 배포 준비 상태 검증")
    print("=" * 60)
    
    # 1. 필수 설정 파일 확인
    print("\n📄 설정 파일 확인...")
    required_files = {
        "requirements.txt": "Python 의존성",
        "runtime.txt": "Python 버전",
        "nixpacks.toml": "Nixpacks 설정",
        "railway.toml": "Railway 설정",
        "main.py": "Railpack 호환 진입점"
    }
    
    for file, desc in required_files.items():
        if Path(file).exists():
            print(f"  ✅ {file} - {desc}")
        else:
            errors.append(f"❌ {file} 파일이 없습니다")
            print(f"  ❌ {file} - 누락")
    
    # 2. 백엔드 구조 확인
    print("\n🏗️  백엔드 구조 확인...")
    backend_paths = {
        "backend/app/main.py": "FastAPI 앱",
        "backend/app/models/schemas.py": "데이터 모델",
        "backend/app/services/embeddings.py": "임베딩 서비스",
        "backend/app/services/search.py": "검색 서비스"
    }
    
    for path, desc in backend_paths.items():
        if Path(path).exists():
            print(f"  ✅ {path} - {desc}")
        else:
            errors.append(f"❌ {path} 파일이 없습니다")
            print(f"  ❌ {path} - 누락")
    
    # 3. 배우 데이터 확인
    print("\n🎭 배우 데이터 확인...")
    data_dir = Path("backend/app/data")
    
    if data_dir.exists():
        emb_path = data_dir / "embeddings.npy"
        meta_path = data_dir / "metadata.json"
        actors_dir = data_dir / "actors"
        
        if emb_path.exists():
            size_mb = emb_path.stat().st_size / 1024 / 1024
            print(f"  ✅ embeddings.npy ({size_mb:.2f} MB)")
        else:
            errors.append("❌ embeddings.npy 파일이 없습니다")
            print("  ❌ embeddings.npy - 누락")
        
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            print(f"  ✅ metadata.json ({len(metadata)}명 배우)")
        else:
            errors.append("❌ metadata.json 파일이 없습니다")
            print("  ❌ metadata.json - 누락")
        
        if actors_dir.exists():
            actor_folders = [d for d in actors_dir.iterdir() if d.is_dir()]
            print(f"  ✅ actors/ ({len(actor_folders)}명 이미지)")
        else:
            warnings.append("⚠️  actors/ 폴더가 없습니다 (옵션)")
            print("  ⚠️  actors/ - 옵션 (이미지 서빙용)")
    else:
        errors.append("❌ backend/app/data/ 디렉토리가 없습니다")
        print("  ❌ data/ 디렉토리 누락")
    
    # 4. requirements.txt 검증
    print("\n📦 Python 의존성 확인...")
    if Path("requirements.txt").exists():
        with open("requirements.txt", 'r') as f:
            reqs = f.read()
        
        critical_deps = [
            ("fastapi", "FastAPI 프레임워크"),
            ("uvicorn", "ASGI 서버"),
            ("insightface", "얼굴 인식"),
            ("numpy", "수치 연산"),
            ("opencv-python-headless", "이미지 처리")
        ]
        
        for dep, desc in critical_deps:
            if dep in reqs.lower():
                print(f"  ✅ {dep} - {desc}")
            else:
                errors.append(f"❌ {dep}가 requirements.txt에 없습니다")
                print(f"  ❌ {dep} - 누락")
        
        # numpy 2.0 경고
        if "numpy" in reqs:
            if "numpy>=1.21.0,<2.0.0" in reqs or "numpy<2.0" in reqs:
                print("  ✅ numpy 버전 제한 (< 2.0)")
            else:
                warnings.append("⚠️  numpy 2.0은 InsightFace와 호환되지 않습니다")
                print("  ⚠️  numpy 버전 제한 권장")
    
    # 5. nixpacks.toml 검증
    print("\n⚙️  Nixpacks 설정 확인...")
    if Path("nixpacks.toml").exists():
        with open("nixpacks.toml", 'r') as f:
            nixpacks = f.read()
        
        checks = [
            ('nixPkgs = ["python312"]', "Python 3.12"),
            ("backend.app.main:app", "FastAPI 앱 경로"),
            ("--host 0.0.0.0", "모든 인터페이스 바인딩"),
            ("--port", "포트 설정"),
            ('PYTHONPATH = "/app"', "PYTHONPATH 설정")
        ]
        
        for check, desc in checks:
            if check in nixpacks:
                print(f"  ✅ {desc}")
            else:
                errors.append(f"❌ nixpacks.toml: {desc} 설정 누락")
                print(f"  ❌ {desc} - 누락")
    
    # 6. railway.toml 검증
    print("\n🚂 Railway 설정 확인...")
    if Path("railway.toml").exists():
        with open("railway.toml", 'r', encoding='utf-8') as f:
            railway = f.read()
        
        if 'builder = "NIXPACKS"' in railway:
            print("  ✅ Nixpacks 빌더 강제 설정")
        else:
            warnings.append("⚠️  railway.toml에 NIXPACKS 빌더 설정이 없습니다")
            print("  ⚠️  Nixpacks 빌더 미설정")
        
        if "healthcheckPath" in railway:
            print("  ✅ 헬스체크 경로 설정")
        else:
            warnings.append("⚠️  헬스체크 경로가 설정되지 않았습니다")
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 검증 결과")
    print("=" * 60)
    
    if not errors and not warnings:
        print("\n🎉 모든 검증 통과! 배포 준비 완료입니다.")
        print("\n다음 단계:")
        print("1. Railway 대시보드에서 Builder를 'Nixpacks'로 변경")
        print("2. git push 후 자동 배포 확인")
        print("3. 배포 로그에서 'using build driver nixpacks' 확인")
        return True
    
    if errors:
        print(f"\n❌ {len(errors)}개의 오류 발견:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)}개의 경고:")
        for warning in warnings:
            print(f"  {warning}")
    
    if errors:
        print("\n❌ 배포 전에 오류를 수정해주세요.")
        return False
    else:
        print("\n⚠️  경고가 있지만 배포 가능합니다.")
        return True

if __name__ == "__main__":
    success = check_deployment_readiness()
    exit(0 if success else 1)
