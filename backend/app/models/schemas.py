"""
Pydantic 스키마 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class MatchResult(BaseModel):
    """단일 매칭 결과"""
    actor_name: str = Field(..., description="배우 이름")
    similarity: float = Field(..., description="유사도 점수 (0~1)")
    image_url: Optional[str] = Field(None, description="배우 이미지 URL")
    is_reference: bool = Field(False, description="레퍼런스 배우 여부")


class MatchResponse(BaseModel):
    """매칭 응답"""
    results: List[MatchResult] = Field(..., description="매칭된 배우 리스트")
    total_actors: int = Field(..., description="전체 인덱스된 배우 수")
    query_info: Optional[dict] = Field(None, description="쿼리 정보")


class BatchMatchRequest(BaseModel):
    """배치 매칭 요청"""
    target_actor: Optional[str] = Field(None, description="타겟 배우 이름 (옵션)")
    top_k: int = Field(3, ge=1, le=10, description="반환할 상위 K값")


class BatchMatchResult(BaseModel):
    """배치 매칭 개별 결과"""
    filename: str = Field(..., description="파일명")
    results: List[MatchResult] = Field(..., description="매칭 결과")
    error: Optional[str] = Field(None, description="에러 메시지")


class BatchMatchResponse(BaseModel):
    """배치 매칭 응답"""
    matches: List[BatchMatchResult] = Field(..., description="각 이미지별 매칭 결과")
    total_processed: int = Field(..., description="처리된 이미지 수")
    total_actors: int = Field(..., description="전체 인덱스된 배우 수")
