# Système d'Orientation Académique - RAG avec ChromaDB

Système de recherche sémantique de formations académiques basé sur une architecture **RAG (Retrieval-Augmented Generation)** avec ChromaDB.

## 📊 Dataset

- **3354 formations** (Licences, Masters, BUT)
- Source : API Parcoursup officielle + données locales
- Métadonnées enrichies : taux d'accès, capacité, sélectivité, académie
- 13 domaines académiques identifiés

## 🚀 Installation Rapide

### 1. Cloner le Projet

```bash
git clone <url-du-repo>
cd TER
```

### 2. Créer l'Environnement Virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 4. ⚠️ IMPORTANT : Réindexer ChromaDB

**Le dossier `data/chroma_db/` n'est PAS dans Git** (trop lourd, peut être reconstruit).

Vous **devez** lancer cette commande après le clone :

```bash
python data\scripts\ingest.py
```

**Temps d'indexation :** ~3 minutes pour 3354 formations

**Sortie attendue :**
```
Demarrage de l'ingestion (Mode Local)...
3354 formations chargees.
Preparation de 3354 documents texte pour l'IA.
Chargement du modele d'embedding multilingue...
Vectorisation en cours avec ChromaDB...
[OK] Index ChromaDB sauvegarde dans : C:\...\data\chroma_db
[OK] Termine ! Vous pouvez maintenant faire des recherches.
```

### 5. Tester la Recherche

```bash
python data\scripts\retrieve.py "licence informatique paris"
```

**Résultats attendus :** Top 3 formations pertinentes avec scores de similarité

## 📁 Structure du Projet

```
TER/
├── data/
│   ├── processed/
│   │   └── formations.json         # 3354 formations enrichies
│   ├── chroma_db/                  # Index vectoriel (généré localement)
│   └── scripts/
│       ├── ingest.py               # Indexation ChromaDB
│       ├── retrieve.py             # Recherche sémantique
│       └── fetch_parcoursup.py     # Enrichissement données
├── README.md
├── report_avancement.tex           # Rapport LaTeX
└── requirements.txt                # Dépendances Python
```

## 🔍 Utilisation

### Recherche Simple

```bash
python data\scripts\retrieve.py "votre requête"
```

**Exemples de requêtes :**
- `"licence informatique paris"`
- `"master droit notarial"`
- `"but génie électrique lyon"`

### Filtrage Automatique

Le système détecte automatiquement :
- **Ville** : "paris", "lyon", "marseille"...
- **Type de diplôme** : "licence", "master", "but"
- **Niveau** : "bac+3", "bac+5"

**Exemple :**
```bash
python data\scripts\retrieve.py "Master droit à Paris"
```
→ Filtre automatique : `ville: paris`, `type_diplome: Master`

## 🔄 Réenrichir les Données (Optionnel)

Si vous voulez mettre à jour le dataset depuis Parcoursup :

```bash
python data\scripts\fetch_parcoursup.py
```

Puis réindexer :

```bash
Remove-Item -Recurse -Force data\chroma_db
python data\scripts\ingest.py
```

## 🛠️ Technologies Utilisées

- **ChromaDB** : Base vectorielle pour la recherche sémantique
- **LangChain** : Pipeline RAG
- **Sentence Transformers** : Embedding multilingue (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Python 3.13**

## ⚠️ Notes Importantes

1. **ChromaDB n'est pas versionné** : Après un `git clone`, vous DEVEZ lancer `ingest.py`
2. **Temps de recherche** : ~200-300ms pour 3354 formations
3. **Taille index** : ~24 MB (ChromaDB)

## 📝 Contributions

- **Dataset** : 600 → 3354 formations (+459%)
- **Domaines** : Amélioration de 29% → 7% de formations "Autre"
- **Métadonnées** : Taux d'accès, capacité, sélectivité (Parcoursup)

## 📄 Documentation Complète

Voir `report_avancement.tex` pour les détails techniques complets.
