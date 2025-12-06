"""
Railway Railpack 호환성을 위한 진입점 파일
실제 앱은 backend/app/main.py에 있습니다.
"""
import sys
import os

# PYTHONPATH 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 실제 FastAPI 앱 임포트
from backend.app.main import app

__all__ = ['app']

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
