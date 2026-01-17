"""Retail Product Agent Backend Vectorstore Services Module."""

from PIL import Image
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, QueryResponse, VectorParams

from backend.app.v1.core.configurations import get_settings
from backend.app.v1.services.embedding import embed_query
from backend.app.v1.services.reranking import rerank_results


def get_vectorstore_client() -> AsyncQdrantClient:
    """
    Initialize and return an AsyncQdrantClient.

    Returns:
        AsyncQdrantClient: The initialized Qdrant client.
    """
    settings = get_settings()
    return AsyncQdrantClient(url=settings.qdrant_url)


async def create_collection(collection_name: str) -> None:
    """
    Create a Qdrant Collection if it does not already exist.

    Args:
        collection_name (str): Name of the collection to create.

    Returns:
        None
    """
    client = get_vectorstore_client()
    collections = await client.get_collections()
    if collection_name in [col.name for col in collections.collections]:
        print(f"Collection '{collection_name}' already exists.")
        return
    await client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )


async def delete_collection(collection_name: str) -> None:
    """
    Delete a Qdrant Collection.

    Args:
        collection_name (str): Name of the collection to delete.

    Returns:
        None
    """
    client = get_vectorstore_client()
    await client.delete_collection(collection_name=collection_name)


async def query_collection(
    query: str | Image.Image,
    collection_name: str,
    add_payload: bool = True,
    search_limit: int = 3,
    rerank: bool = False,
) -> QueryResponse:
    """
    Query a Qdrant collection with an image or text.

    The function embeds the input query using a CLIP model and performs a
    vector search in the specified Qdrant collection. It can handle both
    text and image queries.

    If the query is an image, it is processed and embedded using the CLIP
    image encoder. If the query is text, it is embedded using the CLIP
    text encoder. The text query results can be optionally reranked using a
    CrossEncoder model.

    Args:
        query (str | Image.Image): Text or image query.
        collection_name (str): Name of the collection to query.
        add_payload (bool): Whether to include payload in results.
        search_limit (int): Number of top results to return.
        rerank (bool): Whether to rerank text query results.

    Returns:
        QueryResponse: Results from the vector database.
    """

    client = get_vectorstore_client()

    query_embedding = embed_query(query)
    search_result = await client.query_points(
        collection_name=collection_name,
        query=query_embedding.tolist(),
        with_payload=add_payload,
        limit=search_limit,
    )
    if isinstance(query, str) and rerank:
        search_result.points = rerank_results(search_result.points, query)
    return search_result
