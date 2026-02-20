# ingest.py
# Script d'indexation des formations dans ChromaDB
# Charge le JSON enrichi, cree des documents LangChain et vectorise

import json
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
VECTOR_DB_PATH = BASE_DIR / "data" / "chroma_db"

DATA_CANDIDATES = [
    BASE_DIR / "data" / "processed" / "formations_enriched.json",
    BASE_DIR / "data" / "processed" / "formations_partial.json",
    BASE_DIR / "data" / "processed" / "formations.json",
]


def find_data_path() -> Path:
    """Trouve le meilleur fichier de donnees disponible."""
    for p in DATA_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("Aucun fichier formations trouve")


def load_formations() -> list[dict]:
    path = find_data_path()
    print(f"  Chargement depuis : {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _list_to_str(lst) -> str:
    if not lst:
        return ""
    return ", ".join(str(x) for x in lst)


def create_documents(formations: list[dict]) -> list[Document]:
    """Cree des documents LangChain a partir des formations."""
    docs = []
    for f in formations:
        parts = [
            f"Formation: {f.get('nom', 'Inconnu')}.",
            f"Diplome: {f.get('niveau_diplome', f.get('type_diplome', ''))}.",
            f"Etablissement: {f.get('etablissement', '')} ({f.get('type_etablissement', '')}) a {f.get('ville', '')}.",
            f"Domaine: {f.get('domaine', '')}.",
            f"Niveau entree: {f.get('niveau_entree', '')}. Duree: {f.get('duree', '')}.",
            f"Modalite: {f.get('modalite', '')}.",
            f"Selectivite: {f.get('selectivite', '')}.",
        ]
        if f.get("prerequis_academiques"):
            parts.append(f"Prerequis: {_list_to_str(f['prerequis_academiques'])}.")
        if f.get("competences_acquises"):
            parts.append(f"Competences: {_list_to_str(f['competences_acquises'])}.")
        if f.get("debouches_metiers"):
            parts.append(f"Debouches: {_list_to_str(f['debouches_metiers'])}.")
        if f.get("conseils_candidature"):
            parts.append(f"Conseils: {_list_to_str(f['conseils_candidature'])}.")
        if f.get("alternatives"):
            parts.append(f"Alternatives: {_list_to_str(f['alternatives'])}.")

        text_content = " ".join(parts)
        metadata = {
            "id": f.get("nom", ""),
            "ville": f.get("ville", ""),
            "niveau_entree": f.get("niveau_entree", ""),
            "etablissement": f.get("etablissement", ""),
            "type_diplome": f.get("niveau_diplome", f.get("type_diplome", "")),
            "domaine": f.get("domaine", ""),
            "type_etablissement": f.get("type_etablissement", ""),
            "modalite": f.get("modalite", ""),
            "selectivite": f.get("selectivite", ""),
            "plateforme": f.get("plateforme_candidature", ""),
            "url": f.get("url", ""),
        }
        if f.get("debouches_metiers"):
            metadata["debouches"] = ", ".join(f["debouches_metiers"][:5])
        docs.append(Document(page_content=text_content, metadata=metadata))
    return docs


def main():
    print("=" * 60)
    print("Indexation ChromaDB - Formations enrichies")
    print("=" * 60)

    formations = load_formations()
    if not formations:
        return
    print(f"  {len(formations)} formations chargees.")

    docs = create_documents(formations)
    print(f"  {len(docs)} documents prepares.")

    print("  Chargement du modele d'embedding...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    print("  Vectorisation en cours...")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB_PATH),
        collection_name="orientation_formations",
    )

    print(f"  Index sauvegarde dans : {VECTOR_DB_PATH}")
    print(f"  Termine. {len(docs)} documents indexes.")


if __name__ == "__main__":
    main()
