# Système d'Orientation Académique - RAG avec ChromaDB

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://orientation-rag-app.streamlit.app/)

Système de recherche sémantique de formations académiques basé sur une architecture **RAG (Retrieval-Augmented Generation)** avec ChromaDB. Une interface Streamlit génère un parcours académique personnalisé à partir du profil de l'étudiant.

## Dataset

- **3354 formations** (Licences, Masters, BUT)
- Source : API Parcoursup officielle + données locales
- Métadonnées enrichies : taux d'accès, capacité, sélectivité, académie
- 13 domaines académiques identifiés

## Installation Rapide

### 1. Cloner le Projet

```bash
git clone <url-du-repo>
cd orientation-rag
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

### 4. Configurer les Clés API

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

Ouvrez `.env` et renseignez au moins une clé :
- `OPENAI_API_KEY` si `LLM_PROVIDER=openai` (par défaut)
- `GROQ_API_KEY` si `LLM_PROVIDER=groq` (gratuit, limité)
- rien si `LLM_PROVIDER=ollama` (modèle local, besoin d'Ollama installé)

Sans clé valide, la recherche de formations (ChromaDB) fonctionne quand même, mais la génération de parcours par le LLM échouera.

### 5. IMPORTANT : Réindexer ChromaDB

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

Si vous passez directement par l'interface Streamlit (section suivante), cette étape se lance automatiquement au premier chargement de la page. La lancer à la main avant reste plus rapide à déboguer en cas de problème.

### 6. Tester la Recherche

```bash
python data\scripts\retrieve.py "licence informatique paris"
```

**Résultats attendus :** Top 3 formations pertinentes avec scores de similarité

## Interface Streamlit

L'interface principale du projet est une application Streamlit (`app.py`) : un formulaire de profil étudiant dans la barre latérale, qui génère un parcours académique personnalisé en combinant la recherche ChromaDB et le LLM configuré dans `.env`.

```bash
streamlit run app.py
```

Ouvre automatiquement `http://localhost:8501` dans le navigateur. Le premier chargement est plus lent (construction de l'index ChromaDB si besoin, chargement du modèle d'embedding) ; les chargements suivants utilisent le cache Streamlit (`@st.cache_resource`).

## Déploiement sur Streamlit Community Cloud

1. Poussez le dépôt sur GitHub (le dossier `data/chroma_db/` n'est pas inclus, c'est normal).
2. Sur [share.streamlit.io](https://share.streamlit.io), connectez le dépôt et choisissez `app.py` comme fichier principal.
3. Dans le panneau **Secrets** de l'app, collez les mêmes variables que dans `.env`, par exemple :
   ```toml
   LLM_PROVIDER = "openai"
   OPENAI_API_KEY = "sk-..."
   OPENAI_MODEL = "gpt-4o-mini"
   ```
   `app.py` recopie automatiquement ces secrets dans les variables d'environnement au démarrage, donc le reste du code n'a rien à changer.
4. Le premier chargement sur le Cloud reconstruit l'index ChromaDB à partir de `data/processed/formations.json` (il n'existe pas encore sur le serveur). Cela prend quelques minutes la première fois, puis reste en cache tant que l'app ne redémarre pas.

Deux dépendances supplémentaires existent uniquement pour le Cloud et ne gênent pas l'exécution en local :
- `streamlit` (l'interface elle-même)
- `pysqlite3-binary`, qui remplace le `sqlite3` du système sur Streamlit Cloud (trop ancien pour ChromaDB)

## Structure du Projet

```
orientation-rag/
├── app.py                          # Interface Streamlit (point d'entree)
├── rag/
│   └── models.py                   # Modeles Pydantic (Formation, ProfilEtudiant)
├── src/
│   ├── rag_pipeline.py             # Assemble LLM + vectorstore + prompts
│   ├── vectorstore.py              # Creation/chargement de l'index ChromaDB
│   ├── data_loader.py              # Transforme formations.json en documents
│   ├── prompt_templates.py         # Prompts envoyes au LLM
│   ├── pdf_extractor.py            # Extraction de profil depuis un PDF
│   ├── analyze_data.py             # Statistiques sur le dataset
│   └── api.py                      # API FastAPI (alternative a Streamlit)
├── data/
│   ├── processed/
│   │   └── formations.json         # 3354 formations enrichies
│   ├── chroma_db/                  # Index vectoriel (genere localement, pas dans Git)
│   └── scripts/
│       ├── ingest.py               # Indexation ChromaDB (ligne de commande)
│       ├── retrieve.py             # Recherche semantique (ligne de commande)
│       └── fetch_parcoursup.py     # Enrichissement des donnees
├── tests/
├── docs/
├── .env.example                    # Modele de configuration (cles API, LLM)
├── README.md
└── requirements.txt                # Dependances Python
```

## Utilisation

### Recherche Simple (ligne de commande)

```bash
python data\scripts\retrieve.py "votre requête"
```

**Exemples de requêtes :**
- "licence informatique paris"
- "master droit notarial"
- "but génie électrique lyon"

### Filtrage Automatique

Le système détecte automatiquement :
- **Ville** : "paris", "lyon", "marseille"...
- **Type de diplôme** : "licence", "master", "but"
- **Niveau** : "bac+3", "bac+5"

**Exemple :**
```bash
python data\scripts\retrieve.py "Master droit à Paris"
```
-> Filtre automatique : `ville: paris`, `type_diplome: Master`

## Réenrichir les Données (Optionnel)

Si vous voulez mettre à jour le dataset depuis Parcoursup :

```bash
python data\scripts\fetch_parcoursup.py
```

Puis réindexer :

```bash
Remove-Item -Recurse -Force data\chroma_db
python data\scripts\ingest.py
```

## Technologies Utilisées

- **Streamlit** : interface utilisateur
- **ChromaDB** : base vectorielle pour la recherche sémantique
- **LangChain** : pipeline RAG
- **Sentence Transformers** : embedding multilingue (paraphrase-multilingual-MiniLM-L12-v2)
- **OpenAI / Groq / Ollama** : fournisseur LLM, au choix dans `.env`
- **FastAPI** : API alternative à l'interface Streamlit (`src/api.py`)
- **Python 3.13**

## Notes Importantes

1. **ChromaDB n'est pas versionné** : après un git clone (ou un déploiement Cloud), l'index se reconstruit au premier lancement, à la main avec `ingest.py` ou automatiquement via `app.py`
2. **Temps de recherche** : ~200-300ms pour 3354 formations
3. **Taille index** : ~24 MB (ChromaDB)
4. **Sans clé API valide**, la recherche de formations fonctionne mais la génération de parcours par le LLM échoue

## Contributions

- **Dataset** : 3354 formations
- **Métadonnées** : Taux d'accès, capacité, sélectivité (Parcoursup)
