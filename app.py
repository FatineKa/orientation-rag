# app.py
# Interface Streamlit pour le systeme d'orientation RAG
# Lance avec : streamlit run app.py

import sys
import os
import json
import streamlit as st

# Ajouter le dossier du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.rag_pipeline import PipelineRAG


# Configuration de la page
st.set_page_config(
    page_title="Systeme d'Orientation Intelligent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Style CSS simple
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #4a6fa5 0%, #6b4f8a 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p { color: #ddd; margin: 0.3rem 0 0 0; }
    .step-card {
        background: #f5f7ff;
        border-left: 3px solid #4a6fa5;
        padding: 1rem;
        border-radius: 0 6px 6px 0;
        margin: 0.5rem 0;
    }
    .defi-card {
        background: #fffaf0;
        border-left: 3px solid #d97706;
        padding: 0.8rem;
        border-radius: 0 6px 6px 0;
        margin: 0.4rem 0;
    }
    .alt-card {
        background: #f0fdf4;
        border-left: 3px solid #16a34a;
        padding: 0.8rem;
        border-radius: 0 6px 6px 0;
        margin: 0.4rem 0;
    }
    .stat-box {
        background: white;
        padding: 0.8rem;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .stat-box h3 { margin: 0; font-size: 1.5rem; color: #4a6fa5; }
    .stat-box p { margin: 0; color: #666; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# Chargement du pipeline (mis en cache)
@st.cache_resource(show_spinner="Chargement du pipeline RAG...")
def charger_pipeline():
    pipeline = PipelineRAG()
    pipeline.initialiser(rebuild=False)
    return pipeline


# En-tete
st.markdown("""
<div class="main-header">
    <h1>Systeme d'Orientation Intelligent</h1>
    <p>Generation de parcours academiques personnalises avec RAG + GPT-4o-mini</p>
</div>
""", unsafe_allow_html=True)


# Barre laterale - Formulaire du profil etudiant
with st.sidebar:
    st.header("Profil Etudiant")
    st.caption("Remplis ton profil pour obtenir un parcours personnalise")

    st.subheader("Academique")
    niveau_actuel = st.text_input(
        "Niveau actuel",
        value="Licence 3 Informatique",
        placeholder="Ex: Terminale S, L2 Maths..."
    )
    objectif = st.text_input(
        "Objectif professionnel",
        value="Devenir Data Scientist",
        placeholder="Ex: Devenir ingenieur, medecin..."
    )
    matieres_fortes = st.text_input(
        "Matieres fortes (separees par des virgules)",
        value="Programmation, Mathematiques",
    )
    matieres_faibles = st.text_input(
        "Matieres faibles",
        value="Anglais",
    )

    st.subheader("Competences")
    competences = st.text_input(
        "Competences techniques",
        value="Python, SQL",
    )
    qualites = st.text_input(
        "Qualites personnelles",
        value="Rigoureux, Curieux",
    )
    experiences = st.text_input(
        "Experiences / Stages",
        value="Stage dev web 2 mois",
    )

    st.subheader("Preferences")
    domaines = st.text_input(
        "Domaines d'etudes preferes",
        value="Data Science, Intelligence Artificielle",
    )
    centres_interet = st.text_input(
        "Centres d'interet",
        value="Machine Learning, Environnement",
    )
    type_formation = st.selectbox(
        "Type de formation",
        ["Formation initiale", "Alternance", "A distance"],
    )

    st.subheader("Contraintes")
    geo = st.text_input(
        "Contraintes geographiques",
        value="Paris ou Lyon",
    )
    budget = st.selectbox(
        "Budget",
        ["Public uniquement", "Public ou prive", "Peu importe"],
    )

    # Notes optionnelles
    with st.expander("Notes par matiere (optionnel)"):
        col1, col2 = st.columns(2)
        with col1:
            note_maths = st.number_input("Maths", 0, 20, 16)
            note_info = st.number_input("Info", 0, 20, 15)
        with col2:
            note_physique = st.number_input("Physique", 0, 20, 12)
            note_anglais = st.number_input("Anglais", 0, 20, 10)

    st.divider()
    generer = st.button("Generer mon parcours", type="primary", use_container_width=True)


# Generation du parcours
if generer:
    # Construction du profil
    profil = {
        "niveau_actuel": niveau_actuel,
        "objectif_professionnel": objectif,
        "matieres_fortes": [m.strip() for m in matieres_fortes.split(",") if m.strip()],
        "matieres_faibles": [m.strip() for m in matieres_faibles.split(",") if m.strip()],
        "notes_par_matiere": {
            "Maths": note_maths, "Info": note_info,
            "Physique": note_physique, "Anglais": note_anglais,
        },
        "competences_techniques": [c.strip() for c in competences.split(",") if c.strip()],
        "qualites_personnelles": [q.strip() for q in qualites.split(",") if q.strip()],
        "langues": [{"langue": "Francais", "niveau": "C2"}],
        "experiences_stages": [e.strip() for e in experiences.split(",") if e.strip()],
        "domaines_etudes_preferes": [d.strip() for d in domaines.split(",") if d.strip()],
        "centres_interet": [c.strip() for c in centres_interet.split(",") if c.strip()],
        "type_formation_prefere": type_formation,
        "contraintes_geographiques": geo,
        "budget": budget,
    }

    # Charger le pipeline et generer le parcours
    pipeline = charger_pipeline()

    with st.spinner("Generation du parcours en cours..."):
        try:
            parcours = pipeline.generer_parcours(profil)
        except Exception as e:
            st.error(f"Erreur : {str(e)}")
            st.stop()

    # Affichage des resultats
    st.success("Parcours genere avec succes")

    # Resume
    if parcours.get("resume"):
        st.markdown("### Resume")
        st.info(parcours["resume"])

    # Adequation profil
    if parcours.get("adequation_profil"):
        st.markdown("### Adequation avec ton profil")
        st.markdown(parcours["adequation_profil"])

    # Etapes du parcours
    if parcours.get("etapes"):
        st.markdown("### Etapes du parcours")
        for etape in parcours["etapes"]:
            with st.container():
                st.markdown(f"""
<div class="step-card">
    <strong>Etape {etape.get('numero', '?')}</strong> - {etape.get('titre', '')}
    <br><em>{etape.get('formation_ou_action', '')}</em>
    <br>Etablissement : {etape.get('etablissement', '?')} | Ville : {etape.get('ville', '?')} | Duree : {etape.get('duree', '?')}
    <br>Periode : {etape.get('periode', '')}
</div>
                """, unsafe_allow_html=True)

                if etape.get("description"):
                    st.markdown(etape["description"])

                col1, col2 = st.columns(2)
                with col1:
                    if etape.get("competences_visees"):
                        st.markdown("**Competences visees**")
                        for c in etape["competences_visees"]:
                            st.markdown(f"- {c}")
                with col2:
                    if etape.get("objectifs"):
                        st.markdown("**Objectifs**")
                        for o in etape["objectifs"]:
                            st.markdown(f"- {o}")

                if etape.get("prerequis"):
                    st.markdown("**Prerequis** : " + ", ".join(etape["prerequis"]))

                st.divider()

    # Prerequis globaux
    if parcours.get("prerequis"):
        st.markdown("### Prerequis et demarches")
        prereqs = parcours["prerequis"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Academiques**")
            for p in prereqs.get("academiques", []):
                st.markdown(f"- {p}")
        with col2:
            st.markdown("**Administratifs**")
            for p in prereqs.get("administratifs", []):
                st.markdown(f"- {p}")
        with col3:
            st.markdown("**Calendrier**")
            for p in prereqs.get("calendrier", []):
                st.markdown(f"- {p}")

    # Defis
    if parcours.get("defis"):
        st.markdown("### Defis a anticiper")
        for d in parcours["defis"]:
            st.markdown(f"""
<div class="defi-card">
    <strong>Defi :</strong> {d.get('defi', '')}
    <br><strong>Solution :</strong> {d.get('solution', '')}
</div>
            """, unsafe_allow_html=True)

    # Alternatives
    if parcours.get("alternatives"):
        st.markdown("### Plans alternatifs")
        for a in parcours["alternatives"]:
            st.markdown(f"""
<div class="alt-card">
    <strong>{a.get('situation', '')}</strong>
    <br>-> {a.get('plan_b', '')}
</div>
            """, unsafe_allow_html=True)

    # Conseils
    if parcours.get("conseils_personnalises"):
        st.markdown("### Conseils personnalises")
        for c in parcours["conseils_personnalises"]:
            st.markdown(f"- {c}")

    # Debouches
    if parcours.get("debouches_vises"):
        st.markdown("### Debouches vises")
        cols = st.columns(len(parcours["debouches_vises"]))
        for i, deb in enumerate(parcours["debouches_vises"]):
            with cols[i]:
                st.markdown(f"""
<div class="stat-box">
    <h3>-</h3>
    <p>{deb}</p>
</div>
                """, unsafe_allow_html=True)

    # JSON brut
    with st.expander("Voir le JSON brut"):
        st.json(parcours)

else:
    # Page d'accueil
    st.markdown("### Remplis ton profil dans la barre laterale pour commencer")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
<div class="stat-box">
    <h3>3354</h3>
    <p>Formations indexees</p>
</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div class="stat-box">
    <h3>20</h3>
    <p>Variables par formation</p>
</div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
<div class="stat-box">
    <h3>14</h3>
    <p>Variables profil etudiant</p>
</div>
        """, unsafe_allow_html=True)

    st.markdown("""
    ---
    **Comment ca marche ?**
    1. Remplis ton profil etudiant dans la barre laterale
    2. Le systeme recherche les formations les plus pertinentes (RAG + ChromaDB)
    3. GPT-4o-mini genere un parcours personnalise base sur les donnees reelles
    4. Les resultats s'affichent ici avec etapes, conseils et alternatives
    """)
