import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME

# Directory containing JSON files
DATA_DIR = "restaurant_data"  # All 5 JSONs should be placed here
INDEX_FILE = "restaurant_index.faiss"
CHUNKS_FILE = "restaurant_chunks.json"

embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
flattened_chunks = []

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry in data:
            r_name = entry.get("restaurant_name", "")
            location = entry.get("location", "")
            ctype = entry.get("chunk_type", "")
            content = entry.get("content", {})

            if ctype == "dish":
                name = content.get("dish_name", "")
                price = content.get("price", "")
                desc = content.get("description", "")
                tags = ", ".join(content.get("tags", []))
                chunk = f"{name} at {r_name} ({location}) costs ₹{price}. Tags: {tags}. Description: {desc}"
            elif ctype == "meta":
                intro = content.get("introduction", "")
                hours = content.get("operating_hours", "")
                contact = content.get("contact", "")
                address = content.get("address", "")
                chunk = f"{intro} Address: {address}. Contact: {contact}. Hours: {hours}"
            elif ctype == "features":
                features = ", ".join([f"{k.replace('_', ' ')}: {v}" for k, v in content.items()])
                chunk = f"Restaurant Features at {r_name} ({location}): {features}"
            else:
                continue

            flattened_chunks.append(chunk)

print(f"Total chunks: {len(flattened_chunks)}")

# Compute embeddings
embeddings = embedder.encode(flattened_chunks, show_progress_bar=True)

# Build FAISS index
dimension = embeddings[0].shape[0]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

# Save
faiss.write_index(index, INDEX_FILE)
with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
    json.dump(flattened_chunks, f, indent=2)

print("Indexing complete. Files saved:")
print(f"- {INDEX_FILE}")
print(f"- {CHUNKS_FILE}")
