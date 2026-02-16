import json
import os
from pathlib import Path
from dotenv import load_dotenv

# LangChain & Vector Store
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 1. Config
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "formations.json"
VECTOR_DB_PATH = BASE_DIR / "data" / "chroma_db"

def load_formations():
    if not DATA_PATH.exists():
        print(f"❌ Erreur: Fichier introuvable {DATA_PATH}")
        return []
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_documents(formations):
    docs = []
    for f in formations:
        # Création du texte "riche" pour l'IA
        # On combine les champs pertinents pour que la recherche sémantique fonctionne bien
        text_content = (
            f"Formation: {f.get('nom', 'Inconnu')}. "
            f"Type: {f.get('type_diplome', '')}. "
            f"Établissement: {f.get('etablissement', '')} à {f.get('ville', '')}. "
            f"Niveau: Bac+{f.get('niveau_entree', 0)} vers Bac+{f.get('niveau_sortie', 0)}. "
            f"Domaine: {f.get('domaine', '')}. "
            f"Modalité: {f.get('modalite', '')}."
        )
        
        # Métadonnées pour le filtrage (ville, niveau, type, etc.)
        metadata = {
            "id": f.get("nom"), # ID unique (ou pseudo-unique)
            "ville": f.get("ville"),
            "niveau_entree": f.get("niveau_entree"),
            "niveau_sortie": f.get("niveau_sortie"),
            "etablissement": f.get("etablissement"),
            "type_diplome": f.get("type_diplome"),
            "domaine": f.get("domaine"),
            "url": f.get("url")
        }
        
        docs.append(Document(page_content=text_content, metadata=metadata))
    return docs

def main():
    print("Demarrage de l'ingestion (Mode Local)...")
    
    # 1. Chargement
    formations = load_formations()
    if not formations:
        return
    print(f"{len(formations)} formations chargees.")

    # 2. Préparation des Documents
    docs = create_documents(formations)
    print(f"Preparation de {len(docs)} documents texte pour l'IA.")

    # 3. Embedding (Local - Gratuit)
    print("Chargement du modele d'embedding multilingue (optimise pour le francais)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # 4. Création de l'index Vectoriel avec ChromaDB
    print("Vectorisation en cours avec ChromaDB... (Cela peut prendre quelques secondes)")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB_PATH)
    )
    
    print(f"[OK] Index ChromaDB sauvegarde dans : {VECTOR_DB_PATH}")
    print("[OK] Termine ! Vous pouvez maintenant faire des recherches.")

if __name__ == "__main__":
    main()
