from transformers import pipeline
from config import GENERATION_MODEL_NAME

# Handle the import error by defining MAX_NEW_TOKENS directly if it's not in config
try:
    from config import MAX_NEW_TOKENS
except ImportError:
    MAX_NEW_TOKENS = 256  # Default value if import fails

# Load model pipeline once
gen_pipeline = pipeline("text2text-generation", model=GENERATION_MODEL_NAME)

def generate_answer(query: str, context_chunks: list[str]) -> str:
    context = "\n".join(context_chunks)
    prompt = f"""
You are a helpful restaurant assistant chatbot trained to answer customer questions based on restaurant menus and features. Use only the information in the context to answer concisely and informatively. Avoid adding extra stuff to the answer, only keep the answer relevant to the question. 

Context:
{context}

User Question: {query}
Helpful Answer:"""
    result = gen_pipeline(prompt, max_new_tokens=MAX_NEW_TOKENS)[0]["generated_text"]
    return result.strip()
