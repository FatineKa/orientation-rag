# data_loader.py
# Charge les formations enrichies depuis le JSON
# et les transforme en documents LangChain pour le RAG

import json
from pathlib import Path
from langchain_core.documents import Document


DATA_DIR = Path(__file__).parent.parent / "data"


def charger_json(chemin: str | Path) -> list[dict]:
    """Charge un fichier JSON et retourne une liste de dictionnaires."""
    chemin = Path(chemin)
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)


def _list_to_str(lst: list | None, sep: str = ", ") -> str:
    """Convertit une liste en chaine de caracteres."""
    if not lst:
        return ""
    return sep.join(str(x) for x in lst)


def formation_vers_texte(f: dict) -> str:
    """
    Convertit une formation en texte structure pour le RAG.
    Utilise les 20 variables du schema enrichi.
    """
    parties = []

    # Identification de la formation
    parties.append(f"Formation : {f.get('nom', 'Inconnu')}")
    parties.append(f"Diplome : {f.get('niveau_diplome', '')}")
    parties.append(f"Etablissement : {f.get('etablissement', '')} ({f.get('type_etablissement', '')})")
    parties.append(f"Ville : {f.get('ville', '')}")

    # Caracteristiques
    if f.get("domaine"):
        parties.append(f"Domaine : {f['domaine']}")
    parties.append(f"Duree : {f.get('duree', 'Variable')}")
    parties.append(f"Modalite : {f.get('modalite', 'Formation initiale')}")
    if f.get("langue_enseignement"):
        parties.append(f"Langue d'enseignement : {f['langue_enseignement']}")

    # Admission
    parties.append(f"Niveau d'entree requis : {f.get('niveau_entree', '')}")
    if f.get("prerequis_academiques"):
        parties.append(f"Prerequis : {_list_to_str(f['prerequis_academiques'])}")
    if f.get("selectivite"):
        parties.append(f"Selectivite : {f['selectivite']}")
    if f.get("taux_acces") is not None:
        parties.append(f"Taux d'acces : {f['taux_acces']}%")
    if f.get("frais_scolarite") is not None:
        parties.append(f"Frais de scolarite : {f['frais_scolarite']} euros/an")

    # Administratif
    if f.get("plateforme_candidature"):
        parties.append(f"Plateforme : {f['plateforme_candidature']}")
    if f.get("documents_requis"):
        parties.append(f"Documents requis : {_list_to_str(f['documents_requis'])}")
    if f.get("dates_candidature"):
        d = f["dates_candidature"]
        cal = f"Candidature : {d.get('ouverture', '?')} - {d.get('cloture', '?')}, rentree {d.get('rentree', 'Septembre')}"
        parties.append(cal)

    # Debouches
    if f.get("competences_acquises"):
        parties.append(f"Competences acquises : {_list_to_str(f['competences_acquises'])}")
    if f.get("debouches_metiers"):
        parties.append(f"Debouches metiers : {_list_to_str(f['debouches_metiers'])}")

    # Contexte RAG
    if f.get("defis_courants"):
        parties.append(f"Defis courants : {_list_to_str(f['defis_courants'])}")
    if f.get("conseils_candidature"):
        parties.append(f"Conseils : {_list_to_str(f['conseils_candidature'])}")
    if f.get("alternatives"):
        parties.append(f"Alternatives : {_list_to_str(f['alternatives'])}")

    return "\n".join(parties)


def charger_documents(data_dir: str | Path = None) -> list[Document]:
    """
    Charge les formations et retourne des Documents LangChain.
    Cherche d'abord le fichier enrichi, puis le partiel, puis l'original.
    """
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    documents = []

    # Ordre de priorite des fichiers
    candidates = [
        data_dir / "processed" / "formations_enriched.json",
        data_dir / "processed" / "formations_partial.json",
        data_dir / "processed" / "formations.json",
        data_dir / "formations.json",
    ]

    fichier = None
    for c in candidates:
        if c.exists():
            fichier = c
            break

    if fichier is None:
        print("  ATTENTION: Aucun fichier formations trouve")
        return documents

    formations = charger_json(fichier)

    for f in formations:
        # Metadonnees pour le filtrage dans ChromaDB
        metadata = {
            "nom": f.get("nom", ""),
            "type": "formation",
            "type_diplome": f.get("niveau_diplome", f.get("type_diplome", "")),
            "etablissement": f.get("etablissement", ""),
            "ville": f.get("ville", ""),
            "domaine": f.get("domaine", ""),
            "niveau_entree": f.get("niveau_entree", ""),
            "type_etablissement": f.get("type_etablissement", ""),
            "modalite": f.get("modalite", ""),
            "selectivite": f.get("selectivite", ""),
            "plateforme": f.get("plateforme_candidature", ""),
            "url": f.get("url", ""),
        }

        # Ajouter les debouches en metadonnee
        if f.get("debouches_metiers"):
            metadata["debouches"] = ", ".join(f["debouches_metiers"])

        doc = Document(
            page_content=formation_vers_texte(f),
            metadata=metadata,
        )
        documents.append(doc)

    print(f"  {len(formations)} formations chargees depuis {fichier.name}")
    print(f"  Total : {len(documents)} documents prets pour la vectorisation")
    return documents


if __name__ == "__main__":
    docs = charger_documents()
    if docs:
        print(f"\nExemple de document :")
        print(f"{'=' * 60}")
        print(f"[{docs[0].metadata['type_diplome']}] {docs[0].metadata['nom']}")
        print(docs[0].page_content)
