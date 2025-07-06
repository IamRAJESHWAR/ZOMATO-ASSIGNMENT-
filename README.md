# Restaurant Query Assistant (RAG-based Chatbot)

A Retrieval-Augmented Generation (RAG) system that helps users query information about restaurants, their menus, and features. This project uses natural language processing to provide accurate answers to user queries based on restaurant data.

## Overview

This project implements a Restaurant Query Assistant using a RAG (Retrieval-Augmented Generation) architecture. The system:

1. Scrapes and processes restaurant data from websites
2. Creates a vector knowledge base of restaurant information
3. Uses semantic search to retrieve relevant information
4. Generates natural language responses to user questions

## Project Structure

- `config.py` - Configuration settings for models and parameters
- `knowledge_base_creation.py` - Web scraping for restaurant data collection
- `preprocess_and_index.py` - Data preprocessing and vector index creation
- `retriever.py` - Semantic search functionality for finding relevant information
- `generator.py` - Natural language response generation
- `main.py` - Streamlit web interface for the chatbot

## Dependencies

Key libraries used in this project:
```
transformers==4.30.2
sentence-transformers==2.2.2
faiss-cpu==1.7.4
numpy>=1.20.0
torch>=2.0.0
streamlit>=1.25.0
requests==2.31.0
beautifulsoup4==4.12.2
```

## How It Works

### 1. Data Collection (knowledge_base_creation.py)

This module is responsible for scraping restaurant data from websites:

- Uses BeautifulSoup and requests to scrape restaurant web pages
- Extracts structured data from JSON-LD and HTML elements
- Processes menu items, restaurant details, and features
- Saves the collected data as JSON files in the `restaurant_data/` directory

Key functions:
- `build_knowledge_base(url)`: Builds a knowledge base from a restaurant URL
- `extract_menu_items_ld(ld_blobs)`: Extracts menu items from structured data
- `fallback_menu_items(soup)`: Extracts menu items using HTML parsing as backup

The system collects:
- Restaurant metadata (name, location, contact info)
- Menu items (dish name, price, description, dietary tags)
- Restaurant features (vegetarian options, etc.)

### 2. Data Preprocessing (preprocess_and_index.py)

This script:
- Reads all JSON files from the `restaurant_data/` directory
- Flattens the structured data into text chunks
- Creates embeddings for each chunk using sentence-transformers
- Builds a FAISS vector index for efficient semantic search
- Saves the index and chunk data for retrieval

The preprocessing converts different data types into standardized text chunks:
- Dish chunks: "Pizza at Restaurant Name (Location) costs ₹350. Tags: vegetarian. Description: Classic cheese pizza..."
- Meta chunks: "Restaurant Name is a restaurant located in Location. Address: Full Address..."
- Features chunks: "Restaurant Features at Restaurant Name (Location): vegetarian available: true..."

### 3. Information Retrieval (retriever.py)

This module provides semantic search functionality:
- Takes a user query as input
- Converts the query into an embedding vector
- Uses FAISS to find the most similar chunks in the knowledge base
- Returns the top-k most relevant chunks

The retriever loads:
- A pre-trained sentence transformer model for embedding queries
- The FAISS index for efficient similarity search
- The text chunks corresponding to index positions

### 4. Response Generation (generator.py)

The generator module:
- Uses a pre-trained language model (google/flan-t5-base)
- Takes the user query and retrieved context chunks
- Creates a carefully crafted prompt for the model
- Generates a natural language response based on the provided context

The prompt instructs the model to:
- Answer based only on information in the retrieved context
- Provide concise and informative responses
- Stay relevant to the query

### 5. User Interface (main.py)

A Streamlit-based web interface that:
- Provides a user-friendly input field for questions
- Displays the generated answer
- Shows the top retrieved context chunks for transparency

## Configuration (config.py)

The system's behavior can be adjusted through configuration parameters:
- `EMBEDDING_MODEL_NAME`: Model for semantic search (default: paraphrase-MiniLM-L6-v2)
- `GENERATION_MODEL_NAME`: Model for text generation (default: google/flan-t5-base)
- `RETRIEVAL_TOP_K`: Number of chunks to retrieve (default: 5)
- `MAX_NEW_TOKENS`: Maximum response length (default: 256)

## Data Files

- `restaurant_chunks.json`: Preprocessed text chunks for retrieval
- `restaurant_index.faiss`: Vector index for semantic search
- `restaurant_data/*.json`: Raw restaurant data files

## Usage

### Data Collection
```
python knowledge_base_creation.py <restaurant_url>
```

### Building the Knowledge Base
```
python preprocess_and_index.py
```

### Running the Chatbot
```
streamlit run main.py
```

## Sample Questions

- "What are the vegetarian dishes at Citrus?"
- "What is the price range at Muro Church Street?"
- "Does Sigdi in Mumbai have spicy dishes?"
- "What are the operating hours for The Bawa Kitchen?"
- "Tell me about Ironhill Bengaluru's popular dishes"

## Extending the Project

To add more restaurants:
1. Run `knowledge_base_creation.py` with new restaurant URLs
2. Re-run `preprocess_and_index.py` to update the knowledge base
3. The chatbot will automatically incorporate the new information



HTML (restaurant page)
    ↓
knowledge_base_creation.py
    ↓
Structured JSON chunks (dish/meta/features) → restaurant_data/
    ↓
preprocess_and_index.py
    ↓
Flattened text chunks → Embedded → Indexed (FAISS)
    ↓
User query
    ↓
retriever.py → retrieves top-k relevant chunks
    ↓
generator.py → uses chunks + query to generate answer
    ↓
main.py → shows final result to user
