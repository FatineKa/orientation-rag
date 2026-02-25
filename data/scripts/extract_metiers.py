# extract_metiers.py
# Extrait tous les metiers uniques des debouches des formations
import json
from collections import Counter

with open("/Users/ottosmac/orientation-rag/data/processed/formations_enriched.json", "r", encoding="utf-8") as f:
    formations = json.load(f)

metiers = []
for f in formations:
    debouches = f.get("debouches_metiers", [])
    if debouches:
        metiers.extend(debouches)

# Compter et trier
compteur = Counter(metiers)
metiers_tries = sorted(compteur.items(), key=lambda x: -x[1])

print(f"Total : {len(metiers_tries)} metiers uniques\n")
for metier, count in metiers_tries[:100]:
    print(f"  {metier} ({count})")
