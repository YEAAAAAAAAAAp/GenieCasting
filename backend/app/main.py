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
        print("🚀 서버 시작: Railway 환경 검증...")
        import os
        print(f"   - PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
        print(f"   - HF_HOME: {os.getenv('HF_HOME', 'Not set')}")
        print(f"   - PORT: {os.getenv('PORT', 'Not set')}")
        print(f"   - 데이터 디렉토리: {DATA_DIR}")
        print(f"   - 데이터 디렉토리 존재: {DATA_DIR.exists()}")
        
        print("🚀 서버 시작: 모델 사전 로딩 시작...")
        # 비동기로 모델 로드 (서버 시작 블로킹 방지)
        await asyncio.to_thread(get_insightface_model)
        print("✅ 모델 사전 로딩 완료")
        
        # 인덱스 로드 확인
        print("🚀 배우 인덱스 로딩 시작...")
        INDEX.ensure_loaded()
        actor_count = len(INDEX._emb) if INDEX._emb is not None else 0
        print(f"✅ 배우 인덱스 로드 완료: {actor_count}명")
        
        if actor_count == 0:
            print("⚠️ 경고: 배우 데이터가 비어있습니다!")
            
    except Exception as e:
        print(f"⚠️ 모델 사전 로딩 실패 (첫 요청 시 로드됨): {e}")
        import traceback
        traceback.print_exc()


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
    
    print(f"[DEBUG] match_actors_batch called - files count: {len(files)}, top_k: {top_k}, reference_actor: {reference_actor}")
    print(f"[DEBUG] Memory usage: {sys.getsizeof(files) / 1024 / 1024:.2f} MB")
    
    if not files:
        raise HTTPException(status_code=400, detail="이미지 파일을 업로드하세요")
    
    # 파일 개수 제한 (메모리 보호)
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="한 번에 최대 20개의 이미지만 업로드할 수 있습니다")
    
    outputs = []
    # 레퍼런스 배우 기준으로 업로드된 이미지들을 정렬하기 위한 리스트
    reference_rankings = []
    
    try:
        for idx, f in enumerate(files):
            print(f"[DEBUG] Processing file {idx + 1}/{len(files)}: {f.filename}")
            
            if f.content_type is None or not str(f.content_type).startswith("image/"):
                outputs.append({"filename": f.filename, "error": "이미지 아님"})
                continue
            
            contents = await f.read()
            file_size_mb = len(contents) / 1024 / 1024
            print(f"[DEBUG] File size: {file_size_mb:.2f} MB")
            
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
                print(f"[ERROR] FileNotFoundError for {f.filename}: {e}")
                raise HTTPException(status_code=503, detail=str(e))
            except Exception as e:
                print(f"[ERROR] Exception processing {f.filename}: {e}")
                import traceback
                traceback.print_exc()
                outputs.append({"filename": f.filename, "error": f"처리 실패: {e}"})
            finally:
                # 메모리 정리
                del contents
                gc.collect()
    
    except Exception as e:
        print(f"[CRITICAL ERROR] Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

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
