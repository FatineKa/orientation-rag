"""
data_loader.py — Chargement et préparation des données

Ce module charge les fichiers JSON (formations, métiers) et les transforme
en documents LangChain prêts à être vectorisés.

Pour utiliser vos propres données, remplacez simplement les fichiers JSON
dans le dossier data/ en gardant la même structure.
"""

import json
import os
from pathlib import Path
from langchain.schema import Document


# Chemin par défaut vers le dossier data
DATA_DIR = Path(__file__).parent.parent / "data"


def charger_json(chemin: str | Path) -> list[dict]:
    """Charge un fichier JSON et retourne une liste de dictionnaires."""
    chemin = Path(chemin)
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)


def formation_vers_texte(formation: dict) -> str:
    """
    Convertit une fiche formation en texte structuré lisible,
    optimisé pour le RAG (recherche sémantique).
    """
    parties = [
        f"Formation : {formation['nom']}",
        f"Établissement : {formation['etablissement']} ({formation.get('ville', '')})",
        f"Type : {formation.get('type_formation', '')}",
        f"Domaine : {formation.get('domaine', '')}",
        f"Niveau d'entrée : {formation['niveau_entree']}",
        f"Durée : {formation['duree']}",
        f"\nDescription : {formation.get('description', '')}",
    ]

    if formation.get("prerequis_academiques"):
        parties.append("\nPrérequis académiques :")
        for p in formation["prerequis_academiques"]:
            parties.append(f"  - {p}")

    if formation.get("prerequis_administratifs"):
        parties.append("\nPrérequis administratifs :")
        for p in formation["prerequis_administratifs"]:
            parties.append(f"  - {p}")

    if formation.get("dates_cles"):
        parties.append("\nDates clés :")
        for cle, val in formation["dates_cles"].items():
            parties.append(f"  - {cle.replace('_', ' ').title()} : {val}")

    if formation.get("competences_acquises"):
        parties.append("\nCompétences acquises : " + ", ".join(formation["competences_acquises"]))

    if formation.get("debouches"):
        parties.append("Débouchés : " + ", ".join(formation["debouches"]))

    if formation.get("salaire_moyen_sortie"):
        parties.append(f"Salaire moyen à la sortie : {formation['salaire_moyen_sortie']}")

    if formation.get("taux_insertion"):
        parties.append(f"Taux d'insertion : {formation['taux_insertion']}")

    if formation.get("defis_courants"):
        parties.append("\nDéfis courants :")
        for d in formation["defis_courants"]:
            parties.append(f"  - {d}")

    if formation.get("alternatives"):
        parties.append("\nFormations alternatives : " + ", ".join(formation["alternatives"]))

    if formation.get("parcours_type"):
        parties.append("\nParcours type :")
        for i, etape in enumerate(formation["parcours_type"], 1):
            parties.append(f"  {i}. {etape}")

    return "\n".join(parties)


def metier_vers_texte(metier: dict) -> str:
    """Convertit une fiche métier en texte structuré."""
    parties = [
        f"Métier : {metier['nom']}",
        f"Domaine : {metier.get('domaine', '')}",
        f"\nDescription : {metier.get('description', '')}",
        f"\nNiveau d'études requis : {metier.get('niveau_etudes', '')}",
    ]

    if metier.get("competences_requises"):
        parties.append("Compétences requises : " + ", ".join(metier["competences_requises"]))

    if metier.get("formations_recommandees"):
        parties.append("Formations recommandées : " + ", ".join(metier["formations_recommandees"]))

    if metier.get("salaire_debutant"):
        parties.append(f"Salaire débutant : {metier['salaire_debutant']}")

    if metier.get("salaire_experimenté"):
        parties.append(f"Salaire expérimenté : {metier['salaire_experimenté']}")

    if metier.get("perspectives_emploi"):
        parties.append(f"Perspectives d'emploi : {metier['perspectives_emploi']}")

    if metier.get("secteurs_activite"):
        parties.append("Secteurs d'activité : " + ", ".join(metier["secteurs_activite"]))

    return "\n".join(parties)


def charger_documents(data_dir: str | Path = None) -> list[Document]:
    """
    Charge tous les fichiers de données et retourne des Documents LangChain.

    Chaque document contient :
    - page_content : le texte structuré de la formation ou du métier
    - metadata : les métadonnées (id, type, nom, etc.)

    Args:
        data_dir: Chemin vers le dossier contenant les JSON.
                  Par défaut, utilise le dossier data/ du projet.

    Returns:
        Liste de Documents LangChain prêts à être vectorisés.
    """
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    documents = []

    # Charger les formations
    fichier_formations = data_dir / "formations.json"
    if fichier_formations.exists():
        formations = charger_json(fichier_formations)
        for f in formations:
            doc = Document(
                page_content=formation_vers_texte(f),
                metadata={
                    "id": f.get("id", ""),
                    "type": "formation",
                    "nom": f.get("nom", ""),
                    "etablissement": f.get("etablissement", ""),
                    "domaine": f.get("domaine", ""),
                    "niveau_entree": f.get("niveau_entree", ""),
                }
            )
            documents.append(doc)
        print(f"✓ {len(formations)} formations chargées")

    # Charger les métiers
    fichier_metiers = data_dir / "metiers.json"
    if fichier_metiers.exists():
        metiers = charger_json(fichier_metiers)
        for m in metiers:
            doc = Document(
                page_content=metier_vers_texte(m),
                metadata={
                    "id": m.get("id", ""),
                    "type": "metier",
                    "nom": m.get("nom", ""),
                    "domaine": m.get("domaine", ""),
                }
            )
            documents.append(doc)
        print(f"✓ {len(metiers)} métiers chargés")

    print(f"→ Total : {len(documents)} documents prêts pour la vectorisation")
    return documents


if __name__ == "__main__":
    # Test rapide
    docs = charger_documents()
    for doc in docs:
        print(f"\n{'='*60}")
        print(f"[{doc.metadata['type'].upper()}] {doc.metadata['nom']}")
        print(doc.page_content[:200] + "...")
