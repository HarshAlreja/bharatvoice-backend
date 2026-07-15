"""Retrieval pipeline: embed the customer query, search that business's FAISS
index, return top-k chunks to feed into the LLM prompt."""
from app.vectorstore.faiss_manager import search_index
from app.services.embedding_service import generate_embedding
from app.models.document_chunk import DocumentChunk


def retrieve_context(business_id: int, query: str, top_k: int = 5):
    query_vector = generate_embedding(query)
    vector_ids = search_index(business_id, query_vector, top_k=top_k)

    chunks = (
        DocumentChunk.query.filter(
            DocumentChunk.business_id == business_id,
            DocumentChunk.faiss_vector_id.in_(vector_ids),
        ).all()
    )
    return [c.chunk_text for c in chunks]
