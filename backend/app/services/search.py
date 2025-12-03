import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
EMB_PATH = DATA_DIR / "embeddings.npy"
META_PATH = DATA_DIR / "metadata.json"
ACTOR_IMAGES_DIR = DATA_DIR / "actors"  # optional folder for serving images


class ActorIndex:
    def __init__(self):
        self._loaded = False
        self._emb: Optional[np.ndarray] = None  # shape (N, D) normalized
        self._meta: Optional[List[Dict]] = None  # list of {name, image_rel}

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not EMB_PATH.exists() or not META_PATH.exists():
            # 데이터가 없으면 빈 인덱스로 초기화
            self._emb = np.array([], dtype="float32").reshape(0, 512)
            self._meta = []
            self._loaded = True
            return
        self._emb = np.load(str(EMB_PATH)).astype("float32")
        # ensure normalized rows
        norms = np.linalg.norm(self._emb, axis=1, keepdims=True) + 1e-12
        self._emb = self._emb / norms
        with open(META_PATH, "r", encoding="utf-8") as f:
            self._meta = json.load(f)
        if len(self._meta) != self._emb.shape[0]:
            raise ValueError("Metadata and embeddings row counts do not match")
        self._loaded = True

    def topk(self, query_emb: np.ndarray, k: int = 3) -> List[Tuple[int, float]]:
        self.ensure_loaded()
        assert self._emb is not None
        
        # 데이터가 비어있으면 빈 결과 반환
        if len(self._emb) == 0:
            return []
        
        q = query_emb.astype("float32")
        q = q / (np.linalg.norm(q) + 1e-12)
        # cosine similarity via dot product since rows are normalized
        sims = self._emb @ q
        idx = np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in idx]

    def info(self, idx: int) -> Dict:
        assert self._meta is not None
        return self._meta[idx]

    def find_actor_by_name(self, query_emb: np.ndarray, actor_name: str) -> Optional[Tuple[int, float]]:
        """
        전체 인덱스에서 특정 배우 이름을 찾아서 유사도를 계산
        
        Args:
            query_emb: 쿼리 임베딩 벡터
            actor_name: 찾을 배우 이름
            
        Returns:
            (인덱스, 유사도) 튜플 또는 None (찾지 못한 경우)
        """
        self.ensure_loaded()
        assert self._emb is not None and self._meta is not None
        
        if len(self._emb) == 0:
            return None
        
        # 전체 인덱스에서 배우 이름으로 검색
        actor_name_lower = actor_name.lower().strip()
        for idx, meta in enumerate(self._meta):
            if meta.get("name", "").lower() == actor_name_lower:
                # 유사도 계산
                q = query_emb.astype("float32")
                q = q / (np.linalg.norm(q) + 1e-12)
                score = float(self._emb[idx] @ q)
                return (idx, score)
        
        return None


INDEX = ActorIndex()
