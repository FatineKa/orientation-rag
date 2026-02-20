# process_csv.py
# Phase 1 : Extraction directe et champs calcules
# Lit formations.json et enrichit avec les champs deductibles
# sans appel LLM (duree, type etablissement, plateforme, etc.)
# Produit : data/processed/formations_partial.json

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = BASE_DIR / "data" / "processed" / "formations.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "formations_partial.json"


def niveau_int_to_str(n: int) -> str:
    """Convertit un niveau numerique en label lisible."""
    mapping = {0: "Bac", 1: "Bac+1", 2: "Bac+2", 3: "Bac+3",
               4: "Bac+4", 5: "Bac+5", 8: "Bac+8"}
    return mapping.get(n, f"Bac+{n}")


def calculer_duree(niveau_entree: int, niveau_sortie: int) -> str:
    """Calcule la duree estimee en annees."""
    diff = niveau_sortie - niveau_entree
    if diff <= 0:
        return "Variable"
    return f"{diff} an{'s' if diff > 1 else ''}"


def deduire_type_etablissement(nom_etab: str) -> str:
    """Deduit Public / Prive / Consulaire depuis le nom."""
    nom = nom_etab.lower()
    mots_public = [
        "universite", "iut", "lycee", "ifsi", "ens ", "insa ",
        "inp ", "ecole nationale", "institut national",
        "conservatoire", "faculte", "campus",
    ]
    mots_prive = [
        "prive", "privee", "catholique", "libre", "uco ",
        "escp", "essec", "edhec", "skema", "kedge", "em lyon",
    ]
    mots_consulaire = ["cci", "chambre de commerce", "consulaire"]
    
    for mot in mots_consulaire:
        if mot in nom:
            return "Consulaire"
    for mot in mots_prive:
        if mot in nom:
            return "Prive"
    for mot in mots_public:
        if mot in nom:
            return "Public"
    return "Non renseigne"


def deduire_plateforme(type_diplome: str, niveau_entree: int) -> str:
    """Deduit la plateforme de candidature."""
    t = type_diplome.lower()
    if niveau_entree == 0:
        return "Parcoursup"
    elif "master" in t:
        return "MonMaster"
    elif "doctorat" in t:
        return "Candidature directe"
    else:
        return "Parcoursup"


def enrichir_selectivite(taux_acces, selectivite_existante: str | None) -> str:
    """Enrichit la selectivite depuis le taux d'acces."""
    if selectivite_existante and selectivite_existante not in ("", "Non renseigne"):
        sel = selectivite_existante.lower()
        if "non selective" in sel:
            return "Accessible"
        elif "selective" in sel:
            return "Selectif"
        return selectivite_existante
    if taux_acces is None:
        return "Non renseigne"
    if taux_acces >= 80:
        return "Accessible"
    elif taux_acces >= 40:
        return "Selectif"
    elif taux_acces >= 15:
        return "Tres selectif"
    else:
        return f"Tres selectif (~{int(taux_acces)}%)"


def estimer_frais(type_etablissement: str, type_diplome: str) -> float | None:
    """Estime les frais de scolarite par defaut."""
    t = type_diplome.lower()
    if type_etablissement == "Public":
        if "master" in t:
            return 243.0
        elif "licence" in t or "but" in t:
            return 170.0
        elif "doctorat" in t:
            return 380.0
        else:
            return 170.0
    elif type_etablissement == "Prive":
        return None
    return None


def process_formation(f: dict) -> dict:
    """Transforme une formation au format partiel a 20 variables."""
    niveau_entree_int = f.get("niveau_entree", 0)
    niveau_sortie_int = f.get("niveau_sortie", 3)
    nom_etab = f.get("etablissement", "")
    type_diplome = f.get("type_diplome", "")
    taux = f.get("taux_acces")
    type_etab = deduire_type_etablissement(nom_etab)
    
    return {
        "nom": f.get("nom", ""),
        "etablissement": nom_etab,
        "ville": f.get("ville", ""),
        "type_etablissement": type_etab,
        "niveau_diplome": type_diplome,
        "duree": calculer_duree(niveau_entree_int, niveau_sortie_int),
        "modalite": f.get("modalite", "Formation initiale"),
        "langue_enseignement": None,
        "niveau_entree": niveau_int_to_str(niveau_entree_int),
        "prerequis_academiques": None,
        "selectivite": enrichir_selectivite(taux, f.get("selectivite")),
        "frais_scolarite": estimer_frais(type_etab, type_diplome),
        "plateforme_candidature": deduire_plateforme(type_diplome, niveau_entree_int),
        "documents_requis": None,
        "dates_candidature": None,
        "competences_acquises": None,
        "debouches_metiers": None,
        "defis_courants": None,
        "conseils_candidature": None,
        "alternatives": None,
        "domaine": f.get("domaine", ""),
        "taux_acces": taux,
        "url": f.get("url", ""),
        "academie": f.get("academie", ""),
        "capacite": f.get("capacite"),
        "licences_conseillees": f.get("licences_conseillees", ""),
    }


def main():
    print("=" * 60)
    print("Phase 1 - Extraction directe et champs calcules")
    print("=" * 60)
    
    if not INPUT_PATH.exists():
        print(f"Fichier introuvable : {INPUT_PATH}")
        return
    
    with open(INPUT_PATH, "r", encoding="utf-8") as fp:
        formations = json.load(fp)
    print(f"  {len(formations)} formations chargees depuis {INPUT_PATH.name}")
    
    enriched = [process_formation(f) for f in formations]
    
    # Statistiques
    n_public = sum(1 for f in enriched if f["type_etablissement"] == "Public")
    n_prive = sum(1 for f in enriched if f["type_etablissement"] == "Prive")
    n_nr = sum(1 for f in enriched if f["type_etablissement"] == "Non renseigne")
    print(f"\n  Type : {n_public} Public, {n_prive} Prive, {n_nr} Non renseigne")
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
        json.dump(enriched, fp, ensure_ascii=False, indent=2)
    
    print(f"  Sauvegarde dans : {OUTPUT_PATH}")
    print(f"  {len(enriched)} formations avec ~10/20 variables remplies")


if __name__ == "__main__":
    main()
