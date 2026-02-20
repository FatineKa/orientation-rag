# enrich_formations.py
# Phase 2 : Enrichissement des formations via OpenAI
# Lit formations_partial.json et complete les champs manquants
# avec GPT-4o-mini (prerequis, debouches, competences, etc.)
#
# Usage :
#   python data/scripts/enrich_formations.py              # tout enrichir
#   python data/scripts/enrich_formations.py --limit 10   # tester sur 10
#   python data/scripts/enrich_formations.py --resume     # reprendre

import json
import os
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_PATH = BASE_DIR / "data" / "processed" / "formations_partial.json"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "formations_enriched.json"
CHECKPOINT_PATH = BASE_DIR / "data" / "processed" / "_enrichment_checkpoint.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

BATCH_SIZE = 5
DELAY_BETWEEN_CALLS = 1.0
MAX_RETRIES = 3


# Prompt envoye au LLM pour enrichir les formations
ENRICHMENT_PROMPT = """Tu es un expert du systeme educatif francais (Parcoursup, universites, grandes ecoles).

Pour chaque formation ci-dessous, complete les champs manquants en te basant sur tes connaissances.
Reponds UNIQUEMENT avec un tableau JSON valide, sans texte avant ni apres.

Formations a enrichir :
{formations_input}

Pour chaque formation, retourne un objet JSON avec ces cles :
{{
  "index": <numero de la formation dans la liste>,
  "langue_enseignement": "Francais" ou "Anglais" ou "Bilingue",
  "prerequis_academiques": ["prerequis 1", "prerequis 2", ...],
  "documents_requis": ["document 1", "document 2", ...],
  "dates_candidature": {{"ouverture": "Mois", "cloture": "Mois", "rentree": "Septembre"}},
  "competences_acquises": ["competence 1", "competence 2", ...],
  "debouches_metiers": ["metier 1", "metier 2", ...],
  "defis_courants": ["defi 1", "defi 2"],
  "conseils_candidature": ["conseil 1", "conseil 2"],
  "alternatives": ["formation alternative 1", "formation alternative 2"]
}}

Regles :
- Sois concret et realiste
- 3-5 elements par liste
- Reponds avec un tableau JSON : [{{}}]
"""


def build_formation_summary(f: dict, idx: int) -> str:
    """Resume compact d'une formation pour le prompt."""
    return (
        f"[{idx}] {f.get('nom', '?')} - {f.get('niveau_diplome', '?')} "
        f"a {f.get('etablissement', '?')} ({f.get('ville', '?')}). "
        f"Domaine: {f.get('domaine', '?')}. "
        f"Niveau entree: {f.get('niveau_entree', '?')}. "
        f"Modalite: {f.get('modalite', '?')}. "
        f"Type: {f.get('type_etablissement', '?')}."
    )


def call_openai(prompt: str) -> str:
    """Appelle l'API OpenAI et retourne la reponse texte."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Erreur : openai n'est pas installe")
        sys.exit(1)
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Tu es un expert de l'orientation academique francaise. Reponds uniquement en JSON valide."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4000,
    )
    return response.choices[0].message.content.strip()


def parse_llm_response(response_text: str) -> list[dict]:
    """Parse la reponse JSON du LLM."""
    text = response_text
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
    except json.JSONDecodeError as e:
        print(f"    Erreur JSON : {e}")
        return []
    return []


def apply_enrichment(formation: dict, enrichment: dict) -> dict:
    """Applique les donnees enrichies a une formation."""
    fields = [
        "langue_enseignement", "prerequis_academiques", "documents_requis",
        "dates_candidature", "competences_acquises", "debouches_metiers",
        "defis_courants", "conseils_candidature", "alternatives",
    ]
    for field in fields:
        if field in enrichment and enrichment[field] is not None:
            formation[field] = enrichment[field]
    return formation


def save_checkpoint(formations: list[dict], processed_count: int):
    """Sauvegarde le progres actuel."""
    checkpoint = {"processed_count": processed_count, "formations": formations}
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
        json.dump(checkpoint, fp, ensure_ascii=False, indent=2)


def load_checkpoint() -> tuple[list[dict], int]:
    """Charge le dernier checkpoint."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        return data["formations"], data["processed_count"]
    return None, 0


def enrich_batch(formations: list[dict], start_idx: int) -> list[dict]:
    """Enrichit un lot de formations via OpenAI."""
    summaries = []
    for i, f in enumerate(formations):
        summaries.append(build_formation_summary(f, i))
    
    prompt = ENRICHMENT_PROMPT.format(formations_input="\n".join(summaries))
    
    for attempt in range(MAX_RETRIES):
        try:
            response = call_openai(prompt)
            enrichments = parse_llm_response(response)
            if not enrichments:
                print(f"    Tentative {attempt + 1}/{MAX_RETRIES} - reponse vide")
                time.sleep(2)
                continue
            for en in enrichments:
                idx = en.get("index", -1)
                if 0 <= idx < len(formations):
                    formations[idx] = apply_enrichment(formations[idx], en)
            return formations
        except Exception as e:
            print(f"    Tentative {attempt + 1}/{MAX_RETRIES} - erreur : {e}")
            time.sleep(3)
    
    print(f"    Echec apres {MAX_RETRIES} tentatives pour le batch {start_idx}")
    return formations


def main():
    parser = argparse.ArgumentParser(description="Phase 2 - Enrichissement LLM")
    parser.add_argument("--limit", type=int, default=0, help="Limiter le nombre")
    parser.add_argument("--resume", action="store_true", help="Reprendre")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Phase 2 - Enrichissement LLM (OpenAI)")
    print("=" * 60)
    
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-votre"):
        print("Erreur : cle OpenAI manquante dans .env")
        sys.exit(1)
    
    print(f"  Modele : {OPENAI_MODEL}")
    print(f"  Batch size : {BATCH_SIZE}")
    
    start_from = 0
    if args.resume:
        formations, start_from = load_checkpoint()
        if formations is not None:
            print(f"  Checkpoint trouve : {start_from}/{len(formations)} traitees")
        else:
            print("  Pas de checkpoint, debut depuis le depart")
            args.resume = False
    
    if not args.resume:
        if not INPUT_PATH.exists():
            print(f"Fichier introuvable : {INPUT_PATH}")
            sys.exit(1)
        with open(INPUT_PATH, "r", encoding="utf-8") as fp:
            formations = json.load(fp)
    
    total = len(formations)
    total_to_process = min(args.limit, total - start_from) if args.limit > 0 else total - start_from
    print(f"  {total} formations, {total_to_process} a traiter\n")
    
    end_idx = start_from + total_to_process
    processed = start_from
    
    for batch_start in range(start_from, end_idx, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, end_idx)
        batch = formations[batch_start:batch_end]
        progress = (batch_start - start_from + 1) / total_to_process * 100
        print(f"  [{progress:5.1f}%] Formations {batch_start + 1}-{batch_end}/{total}...")
        
        enriched_batch = enrich_batch(batch, batch_start)
        formations[batch_start:batch_end] = enriched_batch
        processed = batch_end
        
        if processed % 50 == 0 or processed == end_idx:
            save_checkpoint(formations, processed)
            print(f"    Checkpoint sauvegarde ({processed}/{total})")
        
        if batch_end < end_idx:
            time.sleep(DELAY_BETWEEN_CALLS)
    
    # Sauvegarde finale
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
        json.dump(formations, fp, ensure_ascii=False, indent=2)
    
    n_enriched = sum(1 for f in formations[:end_idx] if f.get("debouches_metiers") is not None)
    print(f"\n  {n_enriched}/{end_idx} formations enrichies")
    print(f"  Sauvegarde dans : {OUTPUT_PATH}")
    
    if processed >= total and CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        print("  Checkpoint nettoye")


if __name__ == "__main__":
    main()
