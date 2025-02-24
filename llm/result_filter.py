from typing import Protocol, List
from dataclasses import dataclass
from sentence_transformers import CrossEncoder

@dataclass
class SearchResult:
    metadata: dict
    content: str
    score: float = 0.0

class ResultFilter(Protocol):
    def filter(self, result: List[SearchResult]) -> List[SearchResult]:
        pass

class NoFilter:
    def filter(self, result: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        return result[:top_k]


class RerankFilter: # CrossEncoderReranker
    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model = CrossEncoder(model_name)
    
    def rerank(self, query: str, results: List[SearchResult], k: int) -> List[SearchResult]:
        # 쿼리-문서 쌍 생성
        pairs = [(query, result.content) for result in results]
        
        # Cross-Encoder로 점수 계산
        scores = self.model.predict(pairs)
        
        # 점수 업데이트
        for result, score in zip(results, scores):
            result.score = score
        
        # 점수로 정렬하고 상위 k개 반환
        return sorted(results, key=lambda x: x.score, reverse=True)[:k]

