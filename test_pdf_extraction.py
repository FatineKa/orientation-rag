"""
Script de test pour vérifier l'extraction du PDF existant
"""
import sys
from pathlib import Path

# Vérifier si pdfplumber est installé
try:
    import pdfplumber
    print("[OK] pdfplumber est installe")
except ImportError:
    print("[ERREUR] pdfplumber n'est pas installe")
    print("Installation : pip install pdfplumber")
    sys.exit(1)

# Chemin du PDF
pdf_path = Path(__file__).parent / "data" / "profiles" / "formulaire_karim_messaoudi.pdf"

if not pdf_path.exists():
    print(f"[ERREUR] Fichier introuvable : {pdf_path}")
    sys.exit(1)

print(f"\nTest d'extraction du PDF : {pdf_path.name}")
print("=" * 60)

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"\n[OK] PDF ouvert avec succes")
        print(f"  Nombre de pages : {len(pdf.pages)}")
        
        # Extraire le texte de toutes les pages
        texte_complet = ""
        for i, page in enumerate(pdf.pages, 1):
            texte_page = page.extract_text()
            if texte_page:
                texte_complet += texte_page + "\n"
                print(f"  Page {i} : {len(texte_page)} caracteres extraits")
            else:
                print(f"  Page {i} : [ATTENTION] Aucun texte extrait (possible image/scan)")
        
        print(f"\n[OK] Extraction terminee : {len(texte_complet)} caracteres au total")
        
        # Afficher un aperçu
        print("\n" + "=" * 60)
        print("APERCU DU TEXTE EXTRAIT :")
        print("=" * 60)
        print(texte_complet[:1500])  # Premiers 1500 caractères
        if len(texte_complet) > 1500:
            print("\n[...] (texte tronque)")
        
        print("\n" + "=" * 60)
        
        # Sauvegarder dans un fichier texte pour inspection
        output_path = pdf_path.with_suffix('.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(texte_complet)
        print(f"[OK] Texte complet sauvegarde dans : {output_path}")
        
except Exception as e:
    print(f"\n[ERREUR] Erreur lors de l'extraction : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[SUCCESS] Test reussi ! Le PDF peut etre lu correctement.")
