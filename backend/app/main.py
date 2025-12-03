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
 
    top_k: int = Query(3, ge=1, le=50, description="레퍼런스 배우 기준으로 보여줄 상위 지원자 수"),
    reference_actor: str = Query(None, description="레퍼런스 배우 이름 (선택)"),
):
    if not files:
        raise HTTPException(status_code=400, detail="이미지 파일을 업로드하세요")
    outputs = []
    # 레퍼런스 배우 기준으로 업로드된 이미지들을 정렬하기 위한 리스트
    reference_rankings = []
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
            # 레퍼런스 배우가 지정된 경우와 아닌 경우를 분리 처리
            if reference_actor:
                # 레퍼런스 모드: 전체 인덱스에서 레퍼런스 배우를 찾아서 유사도 계산
                try:
                    reference_result = INDEX.find_actor_by_name(q, reference_actor)
                except Exception as e:
                    outputs.append({
                        "filename": f.filename,
                        "error": f"레퍼런스 배우 검색 중 오류: {str(e)}"
                    })
                    continue
                
                if reference_result is None:
                    # 레퍼런스 배우를 찾지 못한 경우
                    outputs.append({
                        "filename": f.filename,
                        "error": f"레퍼런스 배우 '{reference_actor}'를 데이터베이스에서 찾을 수 없습니다."
                    })
                    continue
                
                reference_idx, reference_score = reference_result
                info = INDEX.info(reference_idx)
                
                # 레퍼런스 모드: 유사도 점수만 반환 (이미지 URL 없음)
                result = {
                    "filename": f.filename,
                    "reference_actor_name": info.get("name", f"Actor {reference_idx}"),
                    "reference_score": reference_score,
                }
                
                # 레퍼런스 배우 기준으로 입력 이미지를 랭킹하기 위해 수집
                reference_rankings.append({
                    "filename": f.filename,
                    "reference_score": reference_score,
                })
                outputs.append(result)
            else:
                # 일반 모드: Top-K 배우 리스트 반환
                top = INDEX.topk(q, k=top_k)
                if len(top) == 0:
                    outputs.append({
                        "filename": f.filename, 
                        "error": "배우 인덱스가 비어있습니다. 먼저 인덱스를 생성해주세요."
                    })
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
        except FileNotFoundError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            outputs.append({"filename": f.filename, "error": f"처리 실패: {e}"})

    # 레퍼런스 배우가 지정된 경우:
    # "레퍼런스 배우 -> 입력된 이미지 리스트업" 형태의 데이터를 추가로 제공
    if reference_actor and reference_rankings:
        # reference_score 기준 내림차순 정렬
        reference_rankings.sort(key=lambda x: x["reference_score"], reverse=True)
        # top_k는 최종적으로 "보여줄 지원자(이미지) 수"이므로 여기에서 슬라이스
        limited_rankings = reference_rankings[:top_k]
        # outputs 중에서 레퍼런스 배우가 실제로 잡힌 이미지들만,
        # 그리고 상위 top_k에 해당하는 이미지들만 그대로 반환
        limited_filenames = {r["filename"] for r in limited_rankings}
        
        # filename을 키로 하는 딕셔너리 생성 (빠른 조회용)
        outputs_dict = {o.get("filename"): o for o in outputs if o.get("filename") in limited_filenames and "reference_score" in o}
        
        # ranked_by_reference의 순서대로 items 정렬
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
