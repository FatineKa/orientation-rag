import json
import os
from pathlib import Path
from dotenv import load_dotenv

# LangChain & Vector Store
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Config
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
VECTOR_DB_PATH = BASE_DIR / "data" / "chroma_db"

def get_unique_cities():
    """Extract distinct cities from the JSON source."""
    json_path = BASE_DIR / "data" / "processed" / "formations.json"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Normalize cities for matching (lowercase)
            return {d['ville'].lower().strip(): d['ville'] for d in data if d.get('ville')}
    except Exception as e:
        print(f"Warning: Could not load cities for auto-filtering: {e}")
        return {}

CITIES_MAP = get_unique_cities()

def detect_filters(query):
    """Simple rule-based filter extractor (The 'Pre-LLM' logic)"""
    filters = {}
    query_lower = query.lower()
    
    # 1. Detect City
    # We look for keys in CITIES_MAP (which are lowercased cities)
    for city_key in CITIES_MAP.keys():
        # Check if the city name appears in the query
        # We need to be careful: "Paris" is good, but "Par" is bad. 
        # A simple "in" check is okay for a POC.
        if f" {city_key} " in f" {query_lower} ": # basic boundary check
            filters['ville'] = city_key # Store the keyword (e.g. 'paris')
            break
            
    # 2. Detect Level (Example)
    if "licence" in query_lower:
        filters['type_diplome'] = "Licence"
    elif "master" in query_lower:
        filters['type_diplome'] = "Master"
        
    return filters

def load_index():
    if not VECTOR_DB_PATH.exists():
        print(f"Erreur: Index introuvable dans {VECTOR_DB_PATH}")
        print("Avez-vous lance ingest.py ?")
        return None

    print("Chargement de l'index vectoriel (ChromaDB)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vectorstore = Chroma(
        persist_directory=str(VECTOR_DB_PATH),
        embedding_function=embeddings
    )
    return vectorstore

def search(vectorstore, query, k=3):
    print(f"\nRecherche : '{query}'")
    
    # 1. Auto-Detect Filters
    matches = detect_filters(query)
    if matches:
        print(f"   [Filtres Detectes] : {matches}")
    
    # 2. Search with Filters
    # Note: efficient filtering requires the vector store to support it. 
    # FAISS + LangChain often filters post-retrieval or requires specific setup.
    # For now, we will fetch more results and filter manually to be safe/easy.
    results = vectorstore.similarity_search_with_score(query, k=k*20) # Fetch even more
    
    filtered_results = []
    for doc, score in results:
        # Apply filters (flexible match)
        match = True
        for key, val in matches.items():
            doc_val = doc.metadata.get(key, '').lower()
            target_val = val.lower()
            
            # Simple substring match for flexible filtering 
            # (e.g. "Paris" matches "Paris 5e")
            if target_val not in doc_val: 
                match = False
                break
        if match:
            filtered_results.append((doc, score))
            
    # Keep top k
    final_results = filtered_results[:k]
    
    if not final_results and matches:
        print("   [INFO] Aucun resultat exact avec les filtres. Recherche elargie...")
        # Fallback: Search without filters
        results = vectorstore.similarity_search_with_score(query, k=k)
        final_results = results

    if not final_results:
        print("   Aucun resultat trouve.")
        return

    for i, (doc, score) in enumerate(final_results):
        print(f"   {i+1}. [Score: {score:.4f}] {doc.metadata.get('nom', 'Nom inconnu')}")
        print(f"      Ville: {doc.metadata.get('ville', '?')}")
        print(f"      Extra: {doc.page_content[:100]}...")


def main():
    vectorstore = load_index()
    if not vectorstore:
        return
    
    # Tests
    search(vectorstore, "Je veux faire de l'intelligence artificielle", k=3)
    search(vectorstore, "Master droit notarial à Paris", k=3)
    search(vectorstore, "Licence art et design", k=3)

if __name__ == "__main__":
    main()
