"""
One FAISS index PER business, saved as indexes/{business_id}.index. Loaded lazily
and cached in memory. Keeps every tenant's knowledge base physically separate.
"""
import os
import faiss
import numpy as np

INDEX_DIR = os.path.join(os.path.dirname(__file__), "indexes")
_cache = {}


def _index_path(business_id: int) -> str:
    return os.path.join(INDEX_DIR, f"{business_id}.index")


def _load_or_create(business_id: int, dim: int = 384):
    if business_id in _cache:
        return _cache[business_id]

    path = _index_path(business_id)
    if os.path.exists(path):
        index = faiss.read_index(path)
    else:
        index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))

    _cache[business_id] = index
    return index


def add_to_index(business_id: int, vector: list) -> int:
    index = _load_or_create(business_id, dim=len(vector))
    vector_id = index.ntotal  # simple incrementing id
    vec = np.array([vector], dtype="float32")
    ids = np.array([vector_id], dtype="int64")
    index.add_with_ids(vec, ids)
    faiss.write_index(index, _index_path(business_id))
    return vector_id


def search_index(business_id: int, query_vector: list, top_k: int = 5) -> list:
    index = _load_or_create(business_id, dim=len(query_vector))
    if index.ntotal == 0:
        return []
    vec = np.array([query_vector], dtype="float32")
    _, ids = index.search(vec, min(top_k, index.ntotal))
    return [int(i) for i in ids[0] if i != -1]


def delete_business_index(business_id: int):
    path = _index_path(business_id)
    if os.path.exists(path):
        os.remove(path)
    _cache.pop(business_id, None)
