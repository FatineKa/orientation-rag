"""
Script d'analyse interactif : Affiche les infos directement dans le terminal
"""
import pandas as pd
from pathlib import Path
import sys
import io

# Forcer l'encodage UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_data_dictionary(df: pd.DataFrame, dataset_name: str):
    """Affiche un tableau descriptif dans le terminal"""
    
    print(f"\n\n{'='*80}")
    print(f"📘 Dictionnaire : {dataset_name.upper()}")
    print(f"Dimensions : {len(df)} lignes × {len(df.columns)} colonnes")
    print(f"{'='*80}")
    
    # En-tête du tableau
    header = f"{'Colonne':<50} | {'Type':<10} | {'% Rempli':<10} | {'Unicité':<15} | {'Exemples (3 premiers)'}"
    print(header)
    print("-" * len(header))
    
    for col in df.columns:
        # 1. Taux de remplissage
        fill_pct = 100 * (1 - df[col].isnull().mean())
        
        # 2. Type simplifié
        dtype = str(df[col].dtype).replace("object", "Texte").replace("float64", "Décimal").replace("int64", "Entier")
        
        # 3. Unicité
        n_unique = df[col].nunique()
        unique_str = f"{n_unique}"
        if n_unique == len(df): unique_str += " (Unique)"
        elif n_unique == 1: unique_str += " (Cst)"
            
        # 4. Exemples clean
        examples = df[col].dropna().unique()[:3]
        ex_str = ", ".join([str(x)[:30] + "..." if len(str(x))>30 else str(x) for x in examples])
        if not ex_str: ex_str = "(Vide)"
        
        # Affichage ligne
        print(f"{col:<50} | {dtype:<10} | {fill_pct:>9.0f}% | {unique_str:<15} | {ex_str}")

def main():
    project_root = Path(__file__).parent.parent if Path(__file__).parent.name != 'scripts' else Path(__file__).parent.parent.parent
    
    data_dir = project_root / "data" / "raw"
    if not data_dir.exists() or not any(data_dir.glob("*.csv")):
        data_dir = project_root / "data"
    
    print(f"📂 Recherche de données dans : {data_dir}")
    
    found = False
    for file_path in data_dir.glob("*.csv"):
        found = True
        name = file_path.stem.replace('_300_lignes', '').capitalize()
        try:
            df = pd.read_csv(file_path, sep=';', on_bad_lines='skip')
            if len(df.columns) < 2: df = pd.read_csv(file_path)
            print_data_dictionary(df, name)
        except Exception as e:
            print(f"❌ Erreur {name} : {e}")
            
    if not found:
        print("❌ Aucun fichier CSV trouvé !")

if __name__ == "__main__":
    main()
