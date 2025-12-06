from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from pathlib import Path
import asyncio

from .models.schemas import MatchResponse, MatchResult
from .services.embeddings import image_embedding, get_insightface_model
from .services.search import INDEX, ACTOR_IMAGES_DIR, DATA_DIR

app = FastAPI(title="Genie Match - Actor Image Matcher", version="1.0.0 (InsightFace)")


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 사전 로드 (첫 요청 시간 단축)"""
    try:
        print("🚀 GenieCasting 서버 시작...")
        
        # 모델 사전 로딩
        await asyncio.to_thread(get_insightface_model)
        
        # 배우 인덱스 로딩
        INDEX.ensure_loaded()
        actor_count = len(INDEX._emb) if INDEX._emb is not None else 0
        
        if actor_count > 0:
            print(f"✅ 서버 준비 완료 - {actor_count}명 배우 데이터 로드됨")
        else:
            print("⚠️ 경고: 배우 데이터가 비어있습니다!")
            
    except Exception as e:
        print(f"⚠️ Startup 경고: {e}")


# Allow local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,allow_headers=["*"]
)

# Optionally serve actor images if available
if ACTOR_IMAGES_DIR.exists():
    app.mount("/actors", StaticFiles(directory=str(ACTOR_IMAGES_DIR)), name="actors")


@app.get("/health")
async def health():
    """Railway 헬스체크용 간단한 엔드포인트"""
    return {"status": "ok", "service": "genie-casting"}


@app.get("/")
async def root():
    """루트 엔드포인트 - Railway 배포 확인용"""
    return {
        "service": "Genie Casting API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "index_status": "/index-status",
            "match": "/match-actors",
            "match_batch": "/match-actors-batch",
            "docs": "/docs"
        }
    }


@app.get("/index-status")
async def index_status():
    """인덱스 상태 확인"""
    INDEX.ensure_loaded()
    return {
        "loaded": INDEX._loaded,
        "actor_count": len(INDEX._emb) if INDEX._emb is not None else 0,
        "has_index": (DATA_DIR / "embeddings.npy").exists() and (DATA_DIR / "metadata.json").exists()
    }


@app.post("/match-actors", response_model=MatchResponse)
async def match_actors(
    file: UploadFile = File(...),
    top_k: int = Query(3, ge=1, le=10, description="반환할 상위 K값"),
):
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일을 업로드하세요")
    # 10MB limit safeguard
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다 (최대 10MB)")

    try:
        image_path = file.filename if file.filename else None
        query = image_embedding(contents, image_path=image_path, use_cache=True)
        if query is None:
            raise HTTPException(status_code=400, detail="이미지에서 얼굴을 감지할 수 없습니다.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"이미지 처리 실패: {e}")

    try:
        top = INDEX.topk(query, k=top_k)
        if len(top) == 0:
            raise HTTPException(
                status_code=503, 
                detail="배우 인덱스가 비어있습니다. 먼저 인덱스를 생성해주세요: python backend/scripts/build_actor_index_insightface.py --dataset-dir dataset"
            )
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {e}")

    results = []
    for idx, score in top:
        info = INDEX.info(idx)
        image_url = None
        if info.get("image_rel"):
            # served under /actors
            image_url = f"/actors/{info['image_rel']}"
        results.append(MatchResult(name=info.get("name", f"Actor {idx}"), score=score, image_url=image_url))

    return MatchResponse(results=results)


@app.post("/match-actors-batch")
async def match_actors_batch(
    files: list[UploadFile] = File(...),
    top_k: int = Query(3, ge=1, le=50, description="레퍼런스 배우 기준으로 보여줄 상위 지원자 수"),
    reference_actor: str = Query(None, description="레퍼런스 배우 이름 (선택)"),
):
    import sys
    import gc
    
    if not files:
        raise HTTPException(status_code=400, detail="이미지 파일을 업로드하세요")
    
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="한 번에 최대 20개의 이미지만 업로드할 수 있습니다")
    
    outputs = []
    reference_rankings = []
    
    try:
        for idx, f in enumerate(files):
            if f.content_type is None or not f.content_type.startswith("image/"):
                outputs.append({"filename": f.filename or f"file_{idx}", "error": "이미지 파일이 아님"})
                continue
            
            content = await f.read()
            
            if len(content) > 10 * 1024 * 1024:
                outputs.append({"filename": f.filename, "error": "파일이 너무 큼(>10MB)"})
                continue
            
            try:
                image_path = f.filename if f.filename else None
                q = image_embedding(content, image_path=image_path, use_cache=True)
                if q is None:
                    outputs.append({"filename": f.filename, "error": "얼굴을 감지할 수 없습니다"})
                    continue
                
                if reference_actor:
                    try:
                        reference_result = INDEX.find_actor_by_name(q, reference_actor)
                    except Exception as e:
                        outputs.append({"filename": f.filename, "error": f"레퍼런스 배우 검색 중 오류: {str(e)}"})
                        continue
                    
                    if reference_result is None:
                        outputs.append({"filename": f.filename, "error": f"레퍼런스 배우 '{reference_actor}'를 찾을 수 없습니다."})
                        continue
                    
                    reference_idx, reference_score = reference_result
                    info = INDEX.info(reference_idx)
                    
                    result = {
                        "filename": f.filename,
                        "reference_actor_name": info.get("name", f"Actor {reference_idx}"),
                        "reference_score": reference_score,
                    }
                    
                    reference_rankings.append({
                        "filename": f.filename,
                        "reference_score": reference_score,
                    })
                    outputs.append(result)
                else:
                    top = INDEX.topk(q, k=top_k)
                    if len(top) == 0:
                        outputs.append({"filename": f.filename, "error": "배우 인덱스가 비어있습니다."})
                        continue
                    
                    items = []
                    for idx, score in top:
                        info = INDEX.info(idx)
                        image_url = f"/actors/{info['image_rel']}" if info.get("image_rel") else None
                        items.append({
                            "name": info.get("name", f"Actor {idx}"), 
                            "score": score, 
                            "image_url": image_url,
                            "is_reference": False
                        })
                    
                    result = {"filename": f.filename, "results": items}
                    outputs.append(result)
            except Exception as e:
                outputs.append({"filename": f.filename, "error": f"처리 실패: {str(e)}"})
            finally:
                del content
                gc.collect()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 처리 중 오류 발생: {str(e)}")

    if reference_actor and reference_rankings:
        reference_rankings.sort(key=lambda x: x["reference_score"], reverse=True)
        limited_rankings = reference_rankings[:top_k]
        limited_filenames = {r["filename"] for r in limited_rankings}
        
        outputs_dict = {o.get("filename"): o for o in outputs if o.get("filename") in limited_filenames and "reference_score" in o}
        
        limited_items = [
            outputs_dict[r["filename"]]
            for r in limited_rankings
            if r["filename"] in outputs_dict
        ]

        return {
            "items": limited_items,
            "ranked_by_reference": limited_rankings,
            "reference_actor": reference_actor,
        }

    return {"items": outputs}
