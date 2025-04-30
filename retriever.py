import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME, RETRIEVAL_TOP_K

INDEX_FILE = "restaurant_index.faiss"
CHUNKS_FILE = "restaurant_chunks.json"

# Load once at import
e = SentenceTransformer(EMBEDDING_MODEL_NAME)
index = faiss.read_index(INDEX_FILE)

with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
    chunks = json.load(f)

def retrieve_chunks(query: str, top_k: int = None):
    if top_k is None:
        top_k = RETRIEVAL_TOP_K
    
    q_embedding = e.encode([query])
    distances, indices = index.search(np.array(q_embedding), top_k)
    return [chunks[i] for i in indices[0]]
