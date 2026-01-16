"""Retail Product Agent Backend Reranking Services Module."""

import os

from dotenv import load_dotenv
from sentence_transformers import CrossEncoder

global _reranker


def get_reranker():
    """Load and return the CrossEncoder reranker model."""
    global _reranker
    if "_reranker" not in globals():
        load_dotenv()
        _reranker = CrossEncoder(os.getenv("rerank_model_name"))
    return _reranker


def rerank_results(scored_points: list, query_text: str, top_n: int = 20) -> list:
    """
    Rerank Qdrant ScoredPoint results using a CrossEncoder model.

    Args:
        scored_points (list): List of ScoredPoint objects from Qdrant query.
        query_text (str): Original query text for reranking.
        top_n (int): Number of top results to rerank.

    Returns:
        list: Reranked list of ScoredPoint objects.
    """
    reranker = get_reranker()

    if not query_text or len(scored_points) == 0:
        return scored_points

    pairs = []
    for point in scored_points[:top_n]:
        candidate_text = point.payload.get("product_description", "")
        pairs.append((query_text, candidate_text))

    scores = reranker.predict(pairs)

    reranked_points = []
    for point, score in zip(scored_points[:top_n], scores, strict=True):
        point_dict = {
            "id": point.id,
            "score": point.score,
            "rerank_score": float(score),
            "payload": point.payload,
            "version": point.version,
        }
        reranked_points.append(point_dict)

    reranked_points = sorted(reranked_points, key=lambda x: x["rerank_score"], reverse=True)

    return reranked_points + scored_points[top_n:]
