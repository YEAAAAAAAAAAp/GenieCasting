from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from pathlib import Path

from .models.schemas import MatchResponse, MatchResult
from .services.embeddings import image_embedding
from .services.search import INDEX, ACTOR_IMAGES_DIR, DATA_DIR

app = FastAPI(title="Genie Match - Actor Image Matcher", version="1.0.0 (InsightFace)")

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
    return {"status": "ok"}


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
    top_k: int = Query(3, ge=1, le=10),
    reference_actor: str = Query(None, description="레퍼런스 배우 이름 (선택)"),
):
    if not files:
        raise HTTPException(status_code=400, detail="이미지 파일을 업로드하세요")
    outputs = []
    for f in files:
        if f.content_type is None or not str(f.content_type).startswith("image/"):
            outputs.append({"filename": f.filename, "error": "이미지 아님"})
            continue
        contents = await f.read()
        if len(contents) > 10 * 1024 * 1024:
            outputs.append({"filename": f.filename, "error": "파일이 너무 큼(>10MB)"})
            continue
        try:
            # 업로드된 파일의 경우 파일명을 기반으로 캐시 경로 생성
            image_path = f.filename if f.filename else None
            q = image_embedding(contents, image_path=image_path, use_cache=True)
            if q is None:
                outputs.append({"filename": f.filename, "error": "얼굴을 감지할 수 없습니다"})
                continue
            top = INDEX.topk(q, k=top_k)
            if len(top) == 0:
                outputs.append({
                    "filename": f.filename, 
                    "error": "배우 인덱스가 비어있습니다. 먼저 인덱스를 생성해주세요."
                })
                continue
            
            items = []
            reference_idx = None
            reference_score = None
            
            # 레퍼런스 배우가 지정된 경우, 해당 배우와의 유사도를 찾음
            if reference_actor:
                for idx, score in top:
                    info = INDEX.info(idx)
                    if info.get("name", "").lower() == reference_actor.lower().strip():
                        reference_idx = idx
                        reference_score = score
                        break
            
            for idx, score in top:
                info = INDEX.info(idx)
                image_url = f"/actors/{info['image_rel']}" if info.get("image_rel") else None
                items.append({
                    "name": info.get("name", f"Actor {idx}"), 
                    "score": score, 
                    "image_url": image_url,
                    "is_reference": info.get("name", "").lower() == reference_actor.lower().strip() if reference_actor else False
                })
            
            result = {"filename": f.filename, "results": items}
            if reference_score is not None:
                result["reference_score"] = reference_score
            outputs.append(result)
        except FileNotFoundError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            outputs.append({"filename": f.filename, "error": f"처리 실패: {e}"})

    return {"items": outputs}
