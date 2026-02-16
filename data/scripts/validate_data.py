import json
import sys
from pathlib import Path
from pydantic import ValidationError

# Ajout du dossier racine au path pour importer rag.models
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

try:
    from rag.models import Formation
except ImportError as e:
    print(f"[ERREUR] Erreur d'import : Impossible de charger rag.models depuis {BASE_DIR}")
    print(f"Détail : {e}")
    sys.exit(1)

def validate_file(json_path: Path):
    if not json_path.exists():
        print(f"[WARN] Fichier {json_path} introuvable. Lancez d'abord process_csv.py.")
        return

    print(f"[INFO] Validation du fichier : {json_path.name} ...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("[ERREUR] Erreur : Le fichier n'est pas un JSON valide.")
            return

    if not isinstance(data, list):
        print("[ERREUR] Erreur : Le JSON doit être une liste d'objets.")
        return

    errors = []
    valid_count = 0
    
    print(f"[INFO] Analyse de {len(data)} entrées...")

    for i, item in enumerate(data):
        try:
            Formation(**item)
            valid_count += 1
        except ValidationError as e:
            errors.append(f"Ligne {i+1} ({item.get('nom', 'Nom inconnu')}): {e}")

    print("-" * 50)
    if not errors:
        print(f"[SUCCES] : {valid_count}/{len(data)} formations valides !")
        print("Le fichier respecte parfaitement le schéma.")
    else:
        print(f"[ECHEC] : {len(errors)} erreurs trouvées sur {len(data)} entrées.")
        print("Premières erreurs :")
        for err in errors[:5]:
            print(f" - {err}")
        print("...")

if __name__ == "__main__":
    target_file = BASE_DIR / "data" / "processed" / "formations.json"
    validate_file(target_file)
