# prompt_templates.py
# Templates de prompts pour la generation de parcours
# Utilise les 20 variables formations et 14 variables profil etudiant

from langchain_core.prompts import PromptTemplate


# Prompt principal pour generer un parcours personnalise
PROMPT_PARCOURS = PromptTemplate(
    input_variables=["profil_etudiant", "context"],
    template="""Tu es un conseiller d'orientation expert dans le systeme educatif francais.
Tu dois generer un parcours academique et professionnel personnalise pour un etudiant,
en te basant sur son profil detaille et sur les informations enrichies des formations.

=== PROFIL COMPLET DE L'ETUDIANT ===
{profil_etudiant}

=== FORMATIONS PERTINENTES (donnees enrichies) ===
{context}

=== INSTRUCTIONS ===
Genere un parcours complet et structure en respectant EXACTEMENT ce format JSON :

{{
  "resume": "Vue d'ensemble du parcours en 3-4 phrases",
  "adequation_profil": "Analyse de l'adequation entre le profil et les formations proposees",
  "etapes": [
    {{
      "numero": 1,
      "titre": "Titre de l'etape",
      "formation_ou_action": "Nom precis de la formation ou action a realiser",
      "etablissement": "Nom de l'etablissement",
      "ville": "Ville",
      "duree": "Duree estimee",
      "periode": "Periode (ex: Septembre 2026 - Juin 2027)",
      "description": "Description detaillee de cette etape",
      "prerequis": ["Prerequis specifiques pour cette etape"],
      "competences_visees": ["Competences que l'etudiant va acquerir"],
      "objectifs": ["Objectif 1", "Objectif 2"]
    }}
  ],
  "prerequis": {{
    "academiques": ["Prerequis academique base sur le profil"],
    "administratifs": ["Demarche administrative (plateforme, documents)"],
    "calendrier": ["Date cle 1 (ouverture/cloture candidatures)"]
  }},
  "defis": [
    {{
      "defi": "Description du defi",
      "solution": "Solution adaptee au profil de l'etudiant"
    }}
  ],
  "alternatives": [
    {{
      "situation": "Si [obstacle]...",
      "plan_b": "Alors [alternative concrete]..."
    }}
  ],
  "conseils_personnalises": [
    "Conseil 1 base sur les matieres fortes/faibles",
    "Conseil 2 base sur les competences techniques",
    "Conseil 3 base sur les contraintes geographiques/budget"
  ],
  "debouches_vises": ["Metier 1 accessible apres le parcours", "Metier 2"]
}}

REGLES IMPORTANTES :
- Utilise les PREREQUIS et DEBOUCHES des formations pour construire un parcours logique
- Adapte les CONSEILS aux forces et faiblesses de l'etudiant
- Propose des ALTERNATIVES basees sur les donnees reelles des formations
- Tiens compte du BUDGET et des CONTRAINTES GEOGRAPHIQUES
- Verifie la SELECTIVITE par rapport aux notes de l'etudiant
- Mentionne les PLATEFORMES de candidature (Parcoursup, MonMaster)
- Reponds UNIQUEMENT avec le JSON, sans texte avant ou apres
"""
)


# Prompt pour resumer un parcours deja genere
PROMPT_RESUME = PromptTemplate(
    input_variables=["parcours"],
    template="""Resume le parcours suivant en 3-4 phrases claires et motivantes,
adaptees a un etudiant qui decouvre ses options.

Parcours :
{parcours}

Resume :"""
)


# Prompt pour verifier la coherence d'un parcours
PROMPT_VALIDATION = PromptTemplate(
    input_variables=["parcours", "profil_etudiant"],
    template="""Analyse le parcours suivant et verifie sa coherence par rapport
au profil de l'etudiant. Identifie les incoherences ou les points manquants.

Profil :
{profil_etudiant}

Parcours propose :
{parcours}

Analyse :
1. Le parcours est-il coherent avec les objectifs de l'etudiant ?
2. Les prerequis sont-ils realisables vu les notes de l'etudiant ?
3. Le calendrier est-il realiste ?
4. Les formations proposees correspondent-elles au budget et a la zone geographique ?
5. Y a-t-il des etapes manquantes ?
6. Suggestions d'amelioration :
"""
)
