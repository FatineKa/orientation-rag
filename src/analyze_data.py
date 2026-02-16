"""
Script d'analyse exploratoire des données Parcoursup
Aide à comprendre la structure et la qualité des données avant nettoyage
"""

import pandas as pd
import os
from pathlib import Path
import sys
import io

# Forcer l'encodage UTF-8 pour la sortie console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def analyze_csv(file_path: str, dataset_name: str):
    """
    Analyse complète d'un fichier CSV
    
    Args:
        file_path: Chemin vers le fichier CSV
        dataset_name: Nom du dataset (pour l'affichage)
    """
    print(f"\n{'='*80}")
    print(f"[ANALYSE] : {dataset_name}")
    print(f"{'='*80}\n")
    
    # Charger les données
    df = pd.read_csv(file_path)
    
    # 1. Informations générales
    print("[1] INFORMATIONS GENERALES")
    print(f"   Nombre de lignes : {len(df)}")
    print(f"   Nombre de colonnes : {len(df.columns)}")
    print(f"   Mémoire utilisée : {df.memory_usage(deep=True).sum() / 1024:.2f} KB\n")
    
    # 2. Liste des colonnes
    print("[2] LISTE DES COLONNES")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:2d}. {col}")
    print()
    
    # 3. Types de données
    print("[3] TYPES DE DONNEES")
    type_counts = df.dtypes.value_counts()
    for dtype, count in type_counts.items():
        print(f"   {dtype}: {count} colonnes")
    print()
    
    # 4. Valeurs manquantes
    print("[4] VALEURS MANQUANTES (Top 10)")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'Colonne': missing.index,
        'Manquantes': missing.values,
        'Pourcentage': missing_pct.values
    })
    missing_df = missing_df[missing_df['Manquantes'] > 0].sort_values('Manquantes', ascending=False).head(10)
    
    if len(missing_df) > 0:
        print(missing_df.to_string(index=False))
    else:
        print("   [OK] Aucune valeur manquante !")
    print()
    
    # 5. Doublons
    print("[5] DOUBLONS")
    duplicates = df.duplicated().sum()
    print(f"   Nombre de lignes en double : {duplicates}")
    if duplicates > 0:
        print(f"   [!] {duplicates / len(df) * 100:.2f}% des donnees sont dupliquees")
    print()
    
    # 6. Aperçu des premières lignes
    print("[6] APERCU DES DONNEES (3 premieres lignes)")
    print(df.head(3).to_string())
    print()
    
    # 7. Statistiques pour colonnes numériques
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        print("[7] STATISTIQUES NUMERIQUES")
        print(df[numeric_cols].describe().to_string())
        print()
    
    # 8. Colonnes catégorielles (valeurs uniques)
    print("[8] COLONNES CATEGORIELLES (nombre de valeurs uniques)")
    categorical_cols = df.select_dtypes(include=['object']).columns[:10]  # Limiter à 10
    for col in categorical_cols:
        unique_count = df[col].nunique()
        print(f"   {col}: {unique_count} valeurs uniques")
        if unique_count <= 10:  # Afficher les valeurs si peu nombreuses
            print(f"      → {df[col].unique()[:10].tolist()}")
    print()
    
    # 9. Recommandations
    print("[9] RECOMMANDATIONS")
    
    # Colonnes avec trop de valeurs manquantes
    very_missing = missing_df[missing_df['Pourcentage'] > 50]
    if len(very_missing) > 0:
        print(f"   [!] {len(very_missing)} colonne(s) avec >50% de valeurs manquantes :")
        for col in very_missing['Colonne']:
            print(f"      - {col}")
        print("   → Envisager de les supprimer")
        print()
    
    # Colonnes avec une seule valeur
    single_value_cols = [col for col in df.columns if df[col].nunique() == 1]
    if len(single_value_cols) > 0:
        print(f"   [!] {len(single_value_cols)} colonne(s) avec une seule valeur unique :")
        for col in single_value_cols:
            print(f"      - {col}: {df[col].unique()[0]}")
        print("   → Ces colonnes n'apportent aucune information")
        print()
    
    # Doublons
    if duplicates > 0:
        print(f"   [!] Supprimer les {duplicates} lignes dupliquees")
        print()
    
    print(f"{'='*80}\n")


def main():
    """Point d'entrée principal"""
    
    # Déterminer le chemin du projet
    current_file = Path(__file__)
    project_root = current_file.parent.parent
    data_dir = project_root / "data"
    
    print("\n[ANALYSE EXPLORATOIRE DES DONNEES PARCOURSUP]")
    print("=" * 80)
    
    # Fichiers à analyser
    files = {
        "licences_300_lignes.csv": "Données Licences",
        "master_300_lignes.csv": "Données Masters"
    }
    
    # Vérifier et analyser chaque fichier
    for filename, dataset_name in files.items():
        file_path = data_dir / filename
        
        if file_path.exists():
            analyze_csv(str(file_path), dataset_name)
        else:
            print(f"[!] Fichier non trouve : {file_path}")
    
    print("\n[OK] ANALYSE TERMINEE\n")
    print("[PROCHAINES ETAPES] :")
    print("   1. Consultez le guide : guide_nettoyage_donnees.md")
    print("   2. Décidez quelles colonnes garder/supprimer")
    print("   3. Créez votre script de nettoyage : clean_data.py")
    print()


if __name__ == "__main__":
    main()
