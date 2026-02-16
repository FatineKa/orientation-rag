"""
prompt_templates.py — Templates de prompts pour la génération de parcours

Les prompts sont le cœur de la qualité de génération.
Ils structurent la réponse du LLM pour obtenir des parcours cohérents.
"""

from langchain.prompts import PromptTemplate


# =============================================================================
# PROMPT PRINCIPAL — Génération de parcours personnalisé
# =============================================================================

PROMPT_PARCOURS = PromptTemplate(
    input_variables=["profil_etudiant", "context"],
    template="""Tu es un conseiller d'orientation expert dans le système éducatif français.
Tu dois générer un parcours académique et professionnel personnalisé pour un étudiant,
en te basant sur son profil et sur les informations fournies sur les formations.

=== PROFIL DE L'ÉTUDIANT ===
{profil_etudiant}

=== INFORMATIONS SUR LES FORMATIONS (données de référence) ===
{context}

=== INSTRUCTIONS ===
Génère un parcours complet et structuré en respectant EXACTEMENT ce format JSON :

{{
  "resume": "Vue d'ensemble du parcours en 3-4 phrases",
  "etapes": [
    {{
      "numero": 1,
      "titre": "Titre de l'étape",
      "formation_ou_action": "Nom précis de la formation ou action à réaliser",
      "etablissement": "Nom de l'établissement (si applicable)",
      "duree": "Durée estimée",
      "periode": "Période (ex: Septembre 2026 - Juin 2027)",
      "description": "Description détaillée de cette étape",
      "objectifs": ["Objectif 1", "Objectif 2"]
    }}
  ],
  "prerequis": {{
    "academiques": ["Prérequis académique 1", "Prérequis académique 2"],
    "administratifs": ["Démarche administrative 1", "Démarche administrative 2"],
    "calendrier": ["Date clé 1", "Date clé 2"]
  }},
  "defis": [
    {{
      "defi": "Description du défi",
      "solution": "Comment s'y préparer ou le surmonter"
    }}
  ],
  "alternatives": [
    {{
      "situation": "Si [obstacle]...",
      "plan_b": "Alors [alternative]..."
    }}
  ],
  "conseils_personnalises": ["Conseil 1 basé sur le profil", "Conseil 2"]
}}

RÈGLES IMPORTANTES :
- Sois précis et concret (noms de formations réels, dates, durées)
- Adapte le parcours au profil spécifique de l'étudiant
- Propose des alternatives réalistes à chaque étape critique
- Utilise les informations des formations fournies quand elles sont pertinentes
- Réponds UNIQUEMENT avec le JSON, sans texte avant ou après
"""
)


# =============================================================================
# PROMPT SIMPLIFIÉ — Pour résumer un parcours déjà généré
# =============================================================================

PROMPT_RESUME = PromptTemplate(
    input_variables=["parcours"],
    template="""Résume le parcours suivant en 3-4 phrases claires et motivantes,
adaptées à un étudiant qui découvre ses options.

Parcours :
{parcours}

Résumé :"""
)


# =============================================================================
# PROMPT DE VALIDATION — Pour vérifier la cohérence d'un parcours
# =============================================================================

PROMPT_VALIDATION = PromptTemplate(
    input_variables=["parcours", "profil_etudiant"],
    template="""Analyse le parcours suivant et vérifie sa cohérence par rapport
au profil de l'étudiant. Identifie les incohérences ou les points manquants.

Profil :
{profil_etudiant}

Parcours proposé :
{parcours}

Analyse :
1. Le parcours est-il cohérent avec les objectifs de l'étudiant ?
2. Les prérequis sont-ils réalisables ?
3. Le calendrier est-il réaliste ?
4. Y a-t-il des étapes manquantes ?
5. Suggestions d'amélioration :
"""
)
