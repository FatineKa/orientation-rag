# Système d'Orientation — Génération de Parcours Personnalisé (RAG)

Module de génération de parcours académiques personnalisés utilisant une architecture **RAG (Retrieval-Augmented Generation)**.

## Fonctionnement

1. L'étudiant fournit son **profil** (niveau, objectif, matières, contraintes)
2. Le système **recherche** les formations pertinentes dans la base vectorielle (ChromaDB)
3. Un **LLM** génère un parcours détaillé et structuré à partir du profil + des données récupérées

## Installation

```bash
# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer le fichier .env
copy .env.example .env
# Editer .env avec votre clé API
```

## Configuration (.env)

Choisir un fournisseur LLM dans le fichier `.env` :

| Fournisseur | Gratuit ? | Qualité | Configuration |
|---|---|---|---|
| **OpenAI** | Non (~$0.01/requête) | Excellente | `OPENAI_API_KEY` |
| **Groq** | Oui (tier limité) | Très bonne | `GROQ_API_KEY` |
| **Ollama** | Oui (local) | Bonne | Installer Ollama + modèle |

## Lancer l'API

```bash
# Option 1 : Démarrer le serveur FastAPI
uvicorn src.api:app --reload --port 8000

# Option 2 : Tester le pipeline directement
python -m src.rag_pipeline
```

Documentation de l'API : http://localhost:8000/docs

## Exemples d'utilisation

### Générer un parcours (via curl)

```bash
curl -X POST http://localhost:8000/generer-parcours \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Alice Dupont",
    "niveau_actuel": "Licence 3 Informatique",
    "objectif": "Devenir Data Scientist",
    "matieres_fortes": ["Programmation", "Mathématiques"],
    "matieres_faibles": ["Anglais"],
    "contraintes": "Rester dans le sud de la France"
  }'
```

### Rechercher des formations

```bash
curl -X POST http://localhost:8000/rechercher-formations \
  -H "Content-Type: application/json" \
  -d '{"query": "cybersécurité master", "top_k": 3}'
```

## Mettre à jour les données

1. Modifier les fichiers dans `data/` (formations.json, metiers.json)
2. Appeler l'endpoint `POST /rebuild-vectorstore` ou relancer le serveur

## Structure du projet

```
TER/
├── data/                    # Données des formations et métiers (JSON)
├── src/
│   ├── data_loader.py       # Chargement JSON → Documents LangChain
│   ├── vectorstore.py       # Gestion ChromaDB (embeddings, recherche)
│   ├── prompt_templates.py  # Templates de prompts pour le LLM
│   ├── rag_pipeline.py      # Pipeline RAG complet
│   └── api.py               # Endpoints FastAPI
├── chroma_db/               # Base vectorielle (auto-générée)
├── .env.example             # Template de configuration
├── requirements.txt         # Dépendances Python
└── README.md                # Ce fichier
```
