"""
Railway Railpack 진입점 파일
실제 FastAPI 앱은 backend/app/main.py에 있습니다.
"""
import sys
import os

# PYTHONPATH 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 환경 변수 설정
os.environ.setdefault('PYTHONPATH', current_dir)
os.environ.setdefault('HF_HOME', os.path.join(current_dir, 'models'))
os.environ.setdefault('TRANSFORMERS_CACHE', os.path.join(current_dir, 'models'))

# 실제 FastAPI 앱 임포트
from backend.app.main import app

__all__ = ['app']

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting GenieCasting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
