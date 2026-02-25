# list_villes.py
# Liste toutes les villes uniques dans formations_enriched.json
import json
from pathlib import Path
from collections import Counter

data_path = Path(__file__).parent.parent / "processed" / "formations_enriched.json"
with open(data_path, "r", encoding="utf-8") as f:
    formations = json.load(f)

# Compter les formations par ville (normalisee en minuscules)
villes_raw = [f.get("ville", "").strip() for f in formations if f.get("ville")]
villes_norm = {}
for v in villes_raw:
    # Normaliser : enlever les arrondissements/cedex pour regrouper
    v_lower = v.lower()
    # Extraire la ville principale
    for sep in [" cedex", "  ", " 1er", " 2e", " 3e", " 4e", " 5e", " 6e",
                " 7e", " 8e", " 9e", " 10e", " 11e", " 12e", " 13e",
                " 14e", " 15e", " 16e", " 17e", " 18e", " 19e", " 20e"]:
        if sep in v_lower:
            v_lower = v_lower.split(sep)[0].strip()
            break
    if v_lower not in villes_norm:
        villes_norm[v_lower] = 0
    villes_norm[v_lower] += 1

# Trier par nombre de formations
villes_triees = sorted(villes_norm.items(), key=lambda x: -x[1])

print(f"Total : {len(formations)} formations dans {len(villes_triees)} villes\n")
print(f"{'Ville':<35} {'Nb formations':>15}")
print("-" * 52)
for ville, count in villes_triees:
    print(f"{ville:<35} {count:>15}")
