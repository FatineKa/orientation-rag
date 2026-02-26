# rag_pipeline.py
# Pipeline RAG pour generer des parcours academiques personnalises
# Ce fichier assemble le LLM, la base vectorielle et le prompt
# Inclut un filtrage geographique pour respecter les contraintes de l'etudiant

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document

from src.vectorstore import initialiser_vectorstore, get_retriever, creer_vectorstore
from src.data_loader import charger_documents
from src.prompt_templates import PROMPT_PARCOURS, PROMPT_SUITE_PARCOURS

load_dotenv()


def get_llm():
    """
    Initialise le modele de langage en fonction du fournisseur
    configure dans le fichier .env (openai, groq ou ollama).
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    
    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    
    elif provider == "ollama":
        from langchain_community.llms import Ollama
        return Ollama(
            model=os.getenv("OLLAMA_MODEL", "mistral"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.3,
        )
    
    else:
        raise ValueError(
            f"Fournisseur LLM inconnu : '{provider}'. "
            "Utilisez 'openai', 'groq' ou 'ollama' dans .env"
        )


def formater_profil(profil: dict) -> str:
    """
    Transforme le dictionnaire du profil etudiant en texte lisible
    pour l'envoyer au LLM. Gere les 14 variables du profil.
    """
    parties = [
        f"Niveau actuel : {profil.get('niveau_actuel', 'Non renseigne')}",
        f"Objectif professionnel : {profil.get('objectif_professionnel', profil.get('objectif', 'En exploration'))}",
    ]

    if profil.get("notes_par_matiere"):
        notes = ", ".join(f"{k}: {v}/20" for k, v in profil["notes_par_matiere"].items())
        parties.append(f"Notes : {notes}")

    if profil.get("competences_techniques"):
        parties.append(f"Competences techniques : {', '.join(profil['competences_techniques'])}")

    if profil.get("qualites_personnelles"):
        parties.append(f"Qualites personnelles : {', '.join(profil['qualites_personnelles'])}")

    if profil.get("langues"):
        langues = ", ".join(f"{l['langue']} ({l['niveau']})" for l in profil["langues"])
        parties.append(f"Langues : {langues}")

    if profil.get("experiences_stages"):
        parties.append(f"Experiences : {', '.join(profil['experiences_stages'])}")

    if profil.get("domaines_etudes_preferes"):
        parties.append(f"Domaines preferes : {', '.join(profil['domaines_etudes_preferes'])}")

    if profil.get("centres_interet"):
        parties.append(f"Centres d'interet : {', '.join(profil['centres_interet'])}")

    if profil.get("type_formation_prefere"):
        parties.append(f"Modalite preferee : {profil['type_formation_prefere']}")

    if profil.get("contraintes_geographiques") or profil.get("contraintes"):
        parties.append(f"Contraintes geo : {profil.get('contraintes_geographiques', profil.get('contraintes', ''))}")

    if profil.get("budget"):
        parties.append(f"Budget : {profil['budget']}")

    return "\n".join(parties)


def construire_requete(profil: dict) -> str:
    """
    Construit la requete de recherche pour la base vectorielle
    a partir des champs cles du profil etudiant.

    Regles importantes :
    - On N'inclut PAS le niveau_actuel (ex: "L2") car cela biaiserait la recherche
      vers des formations du meme niveau au lieu de formations accessibles depuis ce niveau.
    - On limite les centres_interet a 1 seul pour eviter la contamination de domaine
      (ex: "Machine Learning" en centre d'interet ne doit pas tirer vers Informatique
      quand le domaine est Economie).
    - La recherche se concentre sur l'objectif professionnel + le domaine d'etudes.
    """
    elements = []

    if profil.get("objectif_professionnel"):
        elements.append(profil["objectif_professionnel"])
    elif profil.get("objectif"):
        elements.append(profil["objectif"])

    if profil.get("domaines_etudes_preferes"):
        elements.extend(profil["domaines_etudes_preferes"])

    # niveau_actuel volontairement exclus : "L2" biaiserait vers des Licences
    # au lieu de formations accessibles depuis ce niveau (L3, Masters...)

    # Un seul centre d'interet pour eviter la contamination de domaine
    if profil.get("centres_interet"):
        elements.append(profil["centres_interet"][0])

    if profil.get("contraintes_geographiques") or profil.get("contraintes"):
        elements.append(profil.get("contraintes_geographiques", profil.get("contraintes", "")))

    return " ".join(elements) if elements else "orientation formation"


def _extraire_description_formation(page_content: str) -> str:
    """
    Extrait une description concise d'une formation depuis son page_content ChromaDB.
    Cherche dans l'ordre : Competences acquises, Debouches metiers, Domaine.
    Retourne une chaine de 1-2 phrases max (250 chars).
    """
    import re
    lignes = page_content.split("\n")
    extraits = []
    cles = ["Competences acquises", "Debouches metiers", "Domaine", "Diplome"]
    for ligne in lignes:
        for cle in cles:
            if ligne.startswith(cle + " :"):
                valeur = ligne.split(" : ", 1)[-1].strip()
                if valeur:
                    extraits.append(valeur)
                break
        if len(extraits) >= 2:
            break
    if extraits:
        texte = " — ".join(extraits)
        return texte[:250] + ("…" if len(texte) > 250 else "")
    # Fallback : premières lignes utiles
    return page_content[:200].replace("\n", " ").strip()


class PipelineRAG:
    """
    Classe principale du pipeline RAG.
    Elle gere l'initialisation de la base vectorielle,
    la recherche de documents et la generation de parcours.
    """

    def __init__(self):
        self.vectorstore = None
        self.retriever = None
        self.llm = None
        self.chain = None
        self._initialise = False

    def initialiser(self, data_dir: str = None, rebuild: bool = False):
        """
        Initialise le pipeline : charge ou cree la base vectorielle
        et configure le LLM.
        """
        print("=== Initialisation du pipeline RAG ===\n")

        # Determiner le chemin de la base vectorielle
        project_root = Path(__file__).resolve().parent.parent
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
        if not Path(persist_dir).is_absolute():
            persist_dir = str(project_root / persist_dir)

        # Charger ou creer la base vectorielle
        if rebuild or not Path(persist_dir).exists():
            print("Creation de la base vectorielle...")
            documents = charger_documents(data_dir)
            self.vectorstore = creer_vectorstore(documents, persist_dir)
        else:
            print("Chargement de la base vectorielle existante...")
            self.vectorstore = initialiser_vectorstore(data_dir, persist_dir)

        # Configurer le retriever
        self.retriever = get_retriever(self.vectorstore)
        print("Retriever configure\n")

        # Configurer le LLM
        print("Configuration du LLM...")
        self.llm = get_llm()
        print(f"LLM configure ({os.getenv('LLM_PROVIDER', 'openai')})\n")

        self._initialise = True
        print("=== Pipeline pret ===\n")

    # Mapping des academies francaises vers leurs villes principales
    ACADEMIES = {
        "aix-marseille": ["marseille", "aix-en-provence", "avignon", "arles", "salon-de-provence", "gap", "digne"],
        "amiens": ["amiens", "beauvais", "compiegne", "laon", "saint-quentin", "soissons"],
        "besancon": ["besancon", "belfort", "montbeliard", "lons-le-saunier", "vesoul"],
        "bordeaux": ["bordeaux", "pau", "agen", "perigueux", "bayonne", "mont-de-marsan", "libourne"],
        "caen": ["caen", "rouen", "le havre", "cherbourg", "lisieux", "evreux", "alencon", "vire"],
        "clermont-ferrand": ["clermont-ferrand", "aurillac", "le puy-en-velay", "moulins", "montlucon", "vichy"],
        "corse": ["ajaccio", "bastia", "corte"],
        "creteil": ["creteil", "bobigny", "villetaneuse", "aubervilliers", "evry", "melun", "meaux", "fontainebleau"],
        "dijon": ["dijon", "auxerre", "nevers", "macon", "chalon-sur-saone", "le creusot"],
        "grenoble": ["grenoble", "annecy", "chambery", "valence", "bourg-en-bresse"],
        "guadeloupe": ["pointe-a-pitre", "les abymes"],
        "guyane": ["cayenne", "kourou"],
        "la reunion": ["saint-denis", "le tampon", "saint-pierre"],
        "lille": ["lille", "roubaix", "tourcoing", "dunkerque", "calais", "arras", "lens", "douai", "valenciennes"],
        "limoges": ["limoges", "brive", "gueret", "tulle"],
        "lyon": ["lyon", "villeurbanne", "saint-etienne", "roanne", "bourg-en-bresse"],
        "martinique": ["fort-de-france", "schoelcher"],
        "mayotte": ["dembeni", "mamoudzou"],
        "montpellier": ["montpellier", "nimes", "perpignan", "beziers", "carcassonne", "mende", "narbonne"],
        "nancy-metz": ["nancy", "metz", "strasbourg", "epinal", "bar-le-duc", "verdun"],
        "nantes": ["nantes", "angers", "le mans", "laval", "la roche-sur-yon", "saint-nazaire"],
        "nice": ["nice", "cannes", "antibes", "menton", "toulon", "draguignan", "grasse"],
        "orleans-tours": ["orleans", "tours", "blois", "bourges", "chartres", "chateauroux"],
        "paris": ["paris", "nanterre", "orsay", "guyancourt", "versailles", "saint-germain-en-laye",
                   "sceaux", "boulogne-billancourt", "neuilly", "saint-cloud", "massy", "saclay",
                   "cergy", "pontoise", "saint-denis", "montreuil"],
        "poitiers": ["poitiers", "la rochelle", "niort", "angouleme", "chatellerault"],
        "reims": ["reims", "troyes", "chalons-en-champagne", "charleville-mezieres"],
        "rennes": ["rennes", "brest", "quimper", "vannes", "lorient", "saint-brieuc", "saint-malo"],
        "strasbourg": ["strasbourg", "mulhouse", "colmar", "haguenau"],
        "toulouse": ["toulouse", "tarbes", "albi", "montauban", "rodez", "cahors", "auch", "castres", "foix"],
        "versailles": ["versailles", "guyancourt", "saint-quentin-en-yvelines", "poissy", "mantes-la-jolie",
                        "boulogne-billancourt", "nanterre", "cergy", "pontoise", "evry-courcouronnes"],
    }

    def _extraire_villes(self, contrainte_geo: str) -> list[str]:
        """
        Extrait les noms de villes a partir de la contrainte geographique.
        Ex: 'Paris ou Lyon' -> ['paris', 'lyon']
        Ex: 'Marseille' -> ['marseille']
        """
        if not contrainte_geo:
            return []
        import re
        parts = re.split(r'[,]|\bou\b|\bet\b', contrainte_geo.lower())
        villes = [v.strip() for v in parts if v.strip()]
        return villes

    def _trouver_villes_proches(self, ville: str) -> list[str]:
        """
        Trouve les villes proches via le mapping des academies.
        Ex: 'avignon' -> ['marseille', 'aix-en-provence', ...]
        """
        ville = ville.lower()
        for academie, villes_aca in self.ACADEMIES.items():
            if ville in villes_aca or any(ville in v for v in villes_aca):
                # Retourner toutes les villes de l'academie sauf la ville demandee
                return [v for v in villes_aca if v != ville]
        return []

    def _rechercher_avec_filtre_geo(self, requete: str, villes: list[str], top_k: int = 5) -> tuple:
        """
        Recherche des formations avec priorite geographique.
        Retourne (documents, info_geo) avec info_geo indiquant
        les villes trouvees ou les villes proches utilisees.
        """
        over_fetch = max(80, top_k * 16)   # augmente pour avoir plus de candidats a re-classer
        tous_docs = self.vectorstore.similarity_search(requete, k=over_fetch)

        # Separer : ville exacte vs autres
        docs_ville = []
        docs_autres = []

        for doc in tous_docs:
            ville_meta = (doc.metadata.get("ville", "") or "").lower()
            contenu = doc.page_content.lower()
            match = any(v in ville_meta or v in contenu for v in villes)
            if match:
                docs_ville.append(doc)
            else:
                docs_autres.append(doc)

        print(f"  {len(docs_ville)} formations dans la ville exacte (sur {len(tous_docs)} recuperees)")

        # Si on a trouve des formations dans la ville exacte
        if docs_ville:
            resultats = docs_ville[:top_k]
            if len(resultats) < top_k:
                resultats.extend(docs_autres[:top_k - len(resultats)])
            return resultats, {"type": "exact", "villes": villes}

        # Sinon, chercher dans les villes proches (meme academie)
        print(f"  Aucune formation trouvee dans {villes}, recherche de villes proches...")
        villes_proches = []
        for v in villes:
            villes_proches.extend(self._trouver_villes_proches(v))
        villes_proches = list(set(villes_proches))

        if villes_proches:
            docs_proches = []
            for doc in tous_docs:
                ville_meta = (doc.metadata.get("ville", "") or "").lower()
                contenu = doc.page_content.lower()
                match = any(v in ville_meta or v in contenu for v in villes_proches)
                if match:
                    docs_proches.append(doc)

            print(f"  {len(docs_proches)} formations dans les villes proches : {villes_proches[:5]}")

            if docs_proches:
                # Trouver les villes effectivement matchees
                villes_trouvees = set()
                for doc in docs_proches:
                    ville_meta = (doc.metadata.get("ville", "") or "").lower()
                    for v in villes_proches:
                        if v in ville_meta:
                            villes_trouvees.add(v)
                resultats = docs_proches[:top_k]
                if len(resultats) < top_k:
                    resultats.extend(docs_autres[:top_k - len(resultats)])
                return resultats, {
                    "type": "proximite",
                    "ville_demandee": villes,
                    "villes_proches": list(villes_trouvees)[:5]
                }

        # Aucune ville proche trouvee non plus
        return tous_docs[:top_k], {"type": "aucune", "villes": villes}

    def recommander_formations(self, profil: dict, top_k: int = 5) -> tuple:
        """
        Phase 1 : recommande les K formations les plus adaptees au profil.
        Retourne (formations, info_geo).

        Ameliorations :
        - over_fetch augmente pour avoir plus de candidats a re-classer
        - Re-ranking par type_diplome en fonction du niveau actuel :
          L3/M1/M2 -> Masters en priorite | L2 -> Masters puis Licences | Terminale/L1 -> Licences
        - Le domaine de l'etudiant est privilegie dans le re-classement
        """
        if not self._initialise:
            raise RuntimeError(
                "Le pipeline n'est pas initialise. "
                "Appelez pipeline.initialiser() d'abord."
            )

        requete = construire_requete(profil)
        print(f"Requete de recherche : {requete}")

        # Extraire les villes de la contrainte geographique
        contrainte_geo = profil.get("contraintes_geographiques", profil.get("contraintes", ""))
        villes = self._extraire_villes(contrainte_geo)

        # Recherche avec ou sans filtre geographique
        info_geo = None
        if villes:
            print(f"  Filtre geographique actif : {villes}")
            docs, info_geo = self._rechercher_avec_filtre_geo(requete, villes, top_k)
        else:
            docs = self.vectorstore.similarity_search(requete, k=max(50, top_k * 10))
            docs = docs[:max(50, top_k * 10)]

        # --- Filtre dur + Re-ranking : type accessible au niveau, puis domaine de l'etudiant ---
        niveau_actuel   = profil.get("niveau_actuel", "")
        types_preferes  = self._niveau_vers_types_preferes(niveau_actuel)
        domaines_bd     = self._domaines_profil_vers_bd(profil.get("domaines_etudes_preferes", []))
        print(f"  Niveau actuel : {niveau_actuel} -> types preferes : {types_preferes}")
        print(f"  Domaines BD attendus : {domaines_bd}")

        # Filtre dur : garder UNIQUEMENT les types accessibles au niveau de l'etudiant
        # Pas de fallback — un L1 ne voit jamais un Master, meme si peu de Licences disponibles
        docs_filtres = [d for d in docs if d.metadata.get("type_diplome", "") in types_preferes]

        def score_doc(doc):
            td  = doc.metadata.get("type_diplome", "")
            dom = doc.metadata.get("domaine", "")
            # rang du type prefere (0 = meilleur) — priorite absolue sur le domaine
            type_score   = types_preferes.index(td) if td in types_preferes else len(types_preferes) + 10
            # 0 = domaine de l'etudiant, 1 = autre domaine
            domain_score = 0 if (domaines_bd and dom in domaines_bd) else 1
            return (type_score, domain_score)

        docs = sorted(docs_filtres, key=score_doc)[:top_k]
        print(f"{len(docs)} formations recommandees (apres re-ranking domaine + niveau)\n")

        # Extraire les metadonnees de chaque formation (sans doublons)
        formations = []
        seen_rec = set()
        for i, doc in enumerate(docs):
            meta = doc.metadata
            nom   = meta.get("nom", "Formation")
            etab  = meta.get("etablissement", "")
            ville = meta.get("ville", "")
            key = f"{nom.lower().strip()}|{etab.lower().strip()}|{ville.lower().strip()}"
            if key in seen_rec:
                continue
            seen_rec.add(key)
            formations.append({
                "index": i,
                "nom": nom,
                "type": meta.get("type_diplome", meta.get("type", "")),
                "domaine": meta.get("domaine", ""),
                "ville": ville,
                "etablissement": etab,
                "duree": meta.get("duree", ""),
                "url": meta.get("url", ""),
                "extrait": doc.page_content[:300],
                "contenu_complet": doc.page_content,
            })

        return formations, info_geo

    # Cycles : types de diplomes appartenant a chaque voie
    TYPES_CYCLE_UNIV = {"Licence", "Master"}
    TYPES_CYCLE_ALT  = {"BUT"}

    # Mapping domaine UI (selectbox app.py) -> domaines ChromaDB
    # Les cles correspondent exactement aux cles de OBJECTIFS_PAR_DOMAINE dans app.py
    DOMAINE_VERS_BD = {
        "Arts, Culture et Création":       {"Arts, Culture et Création", "ARTS, LETTRES, LANGUES"},
        "Communication et Médias":         {"Communication et Médias", "Communication et Journalisme",
                                            "CULTURE ET COMMUNICATION", "Langues et Communication"},
        "Droit et Sciences Juridiques":    {"Droit et Sciences Juridiques", "DROIT, ECONOMIE, GESTION",
                                            "DROIT, ECONOMIE, GESTION ET SCIENCE POLITIQUE"},
        "Économie et Gestion":             {"Économie et Gestion", "DROIT, ECONOMIE, GESTION",
                                            "DROIT, ECONOMIE, GESTION ET SCIENCE POLITIQUE"},
        "Éducation et Sciences Sociales":  {"Éducation et Sciences Sociales",
                                            "Sciences Humaines et Sociales", "Autre Domaine"},
        "Géographie et Environnement":     {"Géographie et Environnement",
                                            "Environnement et Développement Durable",
                                            "SCIENCES DE LA MER ET DU LITTORAL"},
        "Informatique et Technologies":    {"Informatique et Technologies",
                                            "SCIENCES, TECHNOLOGIES, SANTÉ"},
        "Ingénierie":                      {"Ingénierie", "Informatique et Technologies",
                                            "SCIENCES, TECHNOLOGIES, SANTÉ"},
        "Langues et Communication":        {"Langues et Communication", "ARTS, LETTRES, LANGUES",
                                            "Communication et Médias"},
        "Santé et Médecine":               {"Santé et Médecine", "SCIENCES, TECHNOLOGIES, SANTÉ",
                                            "SCIENCES DE LA SANTE"},
        "Sciences":                        {"Sciences", "SCIENCES, TECHNOLOGIES, SANTÉ",
                                            "SCIENCES ET TECHNOLOGIES"},
        "Sciences Humaines et Sociales":   {"Sciences Humaines et Sociales",
                                            "SCIENCES HUMAINES ET SOCIALES",
                                            "Éducation et Sciences Sociales"},
    }

    def _domaines_profil_vers_bd(self, domaines_profil: list) -> set:
        """
        Convertit les domaines du profil etudiant (labels du selectbox)
        en ensemble de noms de domaines tels qu'ils apparaissent dans ChromaDB.
        La comparaison est tolerante a la casse et aux accents (correspondance partielle).
        """
        domaines_bd = set()
        for dp in domaines_profil:
            # Correspondance exacte dans la table de mapping
            if dp in self.DOMAINE_VERS_BD:
                domaines_bd.update(self.DOMAINE_VERS_BD[dp])
                continue
            # Correspondance partielle (insensible a la casse)
            dp_lower = dp.lower()
            for cle, vals in self.DOMAINE_VERS_BD.items():
                if dp_lower in cle.lower() or cle.lower() in dp_lower:
                    domaines_bd.update(vals)
                    break
        return domaines_bd

    def _niveau_vers_types_preferes(self, niveau_actuel: str) -> list[str]:
        """
        Retourne les types de diplome (type_diplome) dans l'ordre de preference
        en fonction du niveau actuel de l'etudiant.

        Logique :
        - Terminale / L1 / BTS / BUT / Prepa  -> Licence, BUT en priorite
        - L2                                   -> Master en priorite, puis Licence (changement de filiere)
        - L3 / M1 / M2 / Licence Pro           -> Master uniquement
        Permet de recommander des formations accessibles ET pertinentes
        plutot que des formations du meme niveau que l'etudiant.
        """
        n = niveau_actuel.lower()
        if any(x in n for x in ["l3", "licence 3", "m1", "m2", "master", "licence pro"]):
            return ["Master"]
        elif any(x in n for x in ["l2", "licence 2"]):
            return ["Master", "Licence"]
        else:
            # Terminale, L1, BTS, BUT, Prepa
            return ["Licence", "BUT"]

    def _types_diplome_pour_etape(self, titre_etape: str, cycle: str = "universitaire") -> set:
        """
        Determine le(s) type(s) de diplome attendus pour une etape du parcours
        en se basant sur le titre de l'etape (ex: 'L1 Informatique' -> {'Licence'}).

        Logique :
        - Titre contient M1, M2, Master       -> {'Master'}
        - Titre contient L1, L2, L3, Licence  -> {'Licence'}
        - Titre contient BUT                   -> {'BUT'}
        - Titre contient Licence Pro           -> {'Licence', 'Master'}
        - Cycle BUT sans match                 -> {'BUT'}
        - Fallback                             -> {'Licence', 'BUT'}
        """
        t = titre_etape.lower()

        if any(x in t for x in ["m1", "m2", "master"]):
            return {"Master"}
        elif "licence pro" in t or "lp " in t:
            return {"Licence", "Master"}
        elif any(x in t for x in ["l1", "l2", "l3", "licence"]):
            return {"Licence"}
        elif "but" in t:
            return {"BUT"}
        elif cycle == "but":
            return {"BUT"}
        else:
            return {"Licence", "BUT"}

    # Progression par cycle
    PROGRESSION_UNIV = ["L1", "L2", "L3", "M1", "M2"]
    PROGRESSION_BUT  = ["BUT 1", "BUT 2", "BUT 3", "Licence Pro / Insertion"]

    def _detecter_cycle(self, formation_choisie: dict, choix_precedents: list = None) -> str:
        """
        Detecte le cycle de l'etudiant a partir :
        - du type_diplome de la formation qu'il a choisie comme point de depart
        - des choix precedents (si un BUT a deja ete choisi, le cycle est BUT)
        Retourne "universitaire" ou "but".
        """
        # Si l'etudiant a deja fait des choix, on detecte depuis le dernier choix
        if choix_precedents:
            dernier = choix_precedents[-1]
            if dernier.get("cycle") == "BUT/IUT":
                return "but"

        # Sinon, on regarde le type_diplome de la formation choisie comme entree
        type_d = formation_choisie.get("type_diplome", formation_choisie.get("type", ""))
        if type_d == "BUT":
            return "but"
        return "universitaire"

    def _extraire_ville_etape(self, etape: dict, profil: dict) -> str:
        """
        Retourne la ville de recherche pour une etape.
        On utilise TOUJOURS la ville preferee du profil etudiant —
        le LLM ne peut pas imposer une autre ville (ex: Paris pour les Masters).
        """
        return profil.get("contraintes_geographiques", "")

    def _filtrer_par_type(self, docs: list, types_autorises: set) -> list:
        """
        Filtre une liste de documents ChromaDB pour ne garder que
        ceux dont le type_diplome est dans types_autorises.
        """
        resultats = []
        for doc in docs:
            td = doc.metadata.get("type_diplome", "")
            if td in types_autorises:
                resultats.append(doc)
        return resultats

    def _docs_vers_formations(self, docs: list, top_k: int) -> list:
        """
        Convertit une liste de documents ChromaDB en dicts de formation.
        Inclut une description courte issue du contenu indexe (debouches, competences...).
        """
        formations = []
        seen = set()
        for doc in docs[:top_k * 5]:          # sur-fetcher pour avoir assez apres dedup
            if len(formations) >= top_k:
                break
            meta = doc.metadata
            nom = meta.get("nom", "Formation")
            etab = meta.get("etablissement", "")
            ville = meta.get("ville", "")
            # Cle unique : nom complet + etablissement + ville
            key = f"{nom.lower().strip()}|{etab.lower().strip()}|{ville.lower().strip()}"
            if key not in seen:
                seen.add(key)
                # Extraire une description courte : on prend les debouches et competences
                # depuis le page_content (format "Competences acquises : ...\nDebouches : ...")
                description = _extraire_description_formation(doc.page_content)
                formations.append({
                    "nom": nom,
                    "etablissement": meta.get("etablissement", ""),
                    "ville": meta.get("ville", ""),
                    "type_diplome": meta.get("type_diplome", ""),
                    "domaine": meta.get("domaine", ""),
                    "modalite": meta.get("modalite", ""),
                    "url": meta.get("url", ""),
                    "description": description,
                    "source": "base",
                    "exigences_notes": {},
                })
        return formations

    def _rechercher_docs_bruts(self, requete: str, profil: dict, over_fetch: int = 50) -> list:
        """
        Recupere un grand lot de documents ChromaDB (sans filtre de type)
        en respectant STRICTEMENT la contrainte geographique du profil.
        Si une ville est specifiee, on ne retourne QUE les formations de cette ville
        (ou villes proches). Pas de fallback vers d'autres villes.
        """
        contrainte_geo = profil.get("contraintes_geographiques", profil.get("contraintes", ""))
        villes = self._extraire_villes(contrainte_geo)

        docs_tous = self.vectorstore.similarity_search(requete, k=over_fetch)

        if not villes:
            return docs_tous

        # Filtre strict : ville exacte
        docs_ville = [
            d for d in docs_tous
            if any(v in (d.metadata.get("ville", "") or "").lower() for v in villes)
        ]
        if docs_ville:
            return docs_ville

        # Villes proches si aucun resultat exact
        villes_proches = []
        for v in villes:
            villes_proches.extend(self._trouver_villes_proches(v))
        villes_proches = list(set(villes_proches))
        if villes_proches:
            docs_proches = [
                d for d in docs_tous
                if any(v in (d.metadata.get("ville", "") or "").lower() for v in villes_proches)
            ]
            if docs_proches:
                return docs_proches

        # Aucune formation dans cette ville : on elargit la recherche avec plus de docs
        docs_elargi = self.vectorstore.similarity_search(requete, k=over_fetch * 3)
        docs_ville_elargi = [
            d for d in docs_elargi
            if any(v in (d.metadata.get("ville", "") or "").lower() for v in villes)
        ]
        return docs_ville_elargi if docs_ville_elargi else []

    def rechercher_formations_pour_etape(
        self,
        titre_etape: str,
        objectif: str,
        profil: dict,
        top_k: int = 8,
        types_diplome: set = None,
    ) -> list:
        """
        Recherche des formations reelles dans ChromaDB pour une etape du parcours.
        types_diplome : ensemble de valeurs type_diplome a garder (ex. {'Licence', 'Master'}).
                        Si None, aucun filtre de type.
        """
        domaine = " ".join(profil.get("domaines_etudes_preferes", []))
        ville   = profil.get("contraintes_geographiques", "")
        # Requete enrichie : niveau + objectif + domaine + ville pour maximiser la pertinence
        requete = f"{titre_etape} {objectif} {domaine} {ville}".strip()

        docs = self._rechercher_docs_bruts(requete, profil, over_fetch=150)

        if types_diplome:
            docs = self._filtrer_par_type(docs, types_diplome)

        return self._docs_vers_formations(docs, top_k)

    def _predire_niveaux_etapes(self, niveau_actuel: str) -> list:
        """
        Predit les niveaux academiques attendus dans le parcours de l'etudiant,
        en partant de son niveau actuel.
        Retourne une liste de labels comme ['L2', 'L3', 'M1', 'M2'].
        """
        hierarchie = ["L1", "L2", "L3", "M1", "M2"]
        indices_debut = {
            "terminale": 0,      # -> L1, L2, L3, M1, M2
            "bts": 1,            # -> L2, L3, M1, M2
            "but": 1,
            "dut": 1,
            "prepa": 1,
            "l1": 1,             # -> L2, L3, M1, M2
            "l2": 2,             # -> L3, M1, M2
            "l3": 3,             # -> M1, M2
            "licence": 3,
            "m1": 4,             # -> M2
            "m2": 5,
        }
        niveau_lower = niveau_actuel.lower()
        idx = 0
        for cle, val in indices_debut.items():
            if cle in niveau_lower:
                idx = val
                break
        return hierarchie[idx:]

    def _construire_context_formations_par_niveau(self, niveaux: list, objectif: str, profil: dict, top_k: int = 5) -> str:
        """
        Pour chaque niveau predit, interroge ChromaDB et injecte les formations reelles.

        Logique domaine progressif :
        - Premiere moitie des niveaux : formations du DOMAINE ACTUEL de l'etudiant
          (ex: L3 Economie pour un etudiant L2 Eco qui veut etre Data Scientist)
        - Seconde moitie (et au-dela) : formations orientees OBJECTIF PROFESSIONNEL
          (ex: M1/M2 Data Science)
        Cette progression naturelle cree automatiquement une passerelle dans le parcours.
        """
        objectif_clean = objectif.strip()
        domaine_actuel = " ".join(profil.get("domaines_etudes_preferes", []))
        lignes = []
        nb_niveaux = len(niveaux)

        for i_niv, niveau in enumerate(niveaux):
            # Premiere moitie -> requete avec domaine de l'etudiant
            # Seconde moitie  -> requete avec objectif seul (passerelle vers objectif)
            if i_niv < max(1, nb_niveaux // 2) and domaine_actuel:
                requete_niv = f"{niveau} {domaine_actuel}"
            else:
                requete_niv = f"{niveau} {objectif_clean}"

            fU = self.rechercher_formations_pour_etape(
                requete_niv, objectif_clean, profil, top_k,
                types_diplome=self.TYPES_CYCLE_UNIV
            )
            if fU:
                lignes.append(f"\n[{niveau}]")
                for f in fU:
                    lignes.append(f"  - {f['nom']} | {f.get('etablissement', '')} | {f.get('ville', '')}")

        return "\n".join(lignes) if lignes else "(Aucune formation trouvee dans la base pour ces niveaux)"

    def enrichir_options_etapes(
        self,
        parcours: dict,
        profil: dict,
        cycle: str = "universitaire",
        top_k: int = 10,
    ) -> dict:
        """
        Apres generation du LLM, remplace les options de chaque etape
        par des formations REELLES issues de ChromaDB.

        Pour chaque etape :
          - On extrait la ville depuis les suggestions du LLM pour chercher
            des formations dans la meme zone geographique
          - On retourne uniquement les formations du cycle principal
            (Licence/Master pour cycle universitaire, BUT pour cycle BUT)
          - Pas d'alternatives : on se concentre sur le parcours de l'etudiant

        Chaque etape recoit :
          etape["options"]         : formations reelles du cycle principal
          etape["options_ia"]      : suggestions originales du LLM (archivees)
          etape["ville_recherche"] : ville utilisee pour la recherche
        """
        if not parcours.get("etapes"):
            return parcours

        objectif = profil.get("objectif_professionnel", profil.get("objectif", ""))
        ville_pref = self._extraire_ville_etape(parcours["etapes"][0], profil) if parcours["etapes"] else ""

        # --- Logique : 1 recherche par PHASE, pas par etape ---
        # Une Licence = 1 programme de 3 ans (L1/L2/L3 = meme formation, meme universite)
        # Un Master = 1 programme de 2 ans (M1/M2 = meme formation, meme universite)
        # On cherche UNE fois la meilleure Licence et UNE fois le meilleur Master,
        # puis on assigne la meme formation a toutes les etapes de chaque phase.

        # 1. Chercher la meilleure LICENCE dans la ville preferee
        domaine = " ".join(profil.get("domaines_etudes_preferes", []))
        profil_licence = {**profil, "contraintes_geographiques": ville_pref}
        options_licence = self.rechercher_formations_pour_etape(
            f"Licence {domaine}", objectif, profil_licence, top_k,
            types_diplome={"Licence"},
        )
        # Fallback licence sans contrainte geo
        if not options_licence:
            profil_sans_geo = {**profil, "contraintes_geographiques": ""}
            options_licence = self.rechercher_formations_pour_etape(
                f"Licence {domaine}", objectif, profil_sans_geo, top_k,
                types_diplome={"Licence"},
            )

        # 2. Chercher le meilleur MASTER pour l'objectif (national, par debouches)
        options_master = self._rechercher_master_par_objectif(objectif, profil, top_k)

        # 3. Chercher le meilleur BUT si cycle BUT
        options_but = []
        if cycle == "but":
            options_but = self.rechercher_formations_pour_etape(
                f"BUT {domaine}", objectif, profil_licence, top_k,
                types_diplome={"BUT"},
            )

        # 4. Assigner les formations aux etapes
        for etape in parcours["etapes"]:
            titre = etape.get("titre", "")
            etape["options_ia"] = etape.get("options", [])
            types_etape = self._types_diplome_pour_etape(titre, cycle)

            if types_etape == {"Master"}:
                etape["options"] = options_master
                etape["ville_recherche"] = "France (mobilité Master)"
            elif types_etape == {"BUT"}:
                etape["options"] = options_but
                etape["ville_recherche"] = ville_pref
            else:
                # Licence (L1/L2/L3) = meme formation
                etape["options"] = options_licence
                etape["ville_recherche"] = ville_pref

            etape["options_alternatives"] = []

        return parcours

    def _moyenne_notes(self, profil: dict) -> float:
        """Calcule la moyenne des notes de l'etudiant (exclut les 0)."""
        notes = profil.get("notes_par_matiere", {})
        vals = [v for v in notes.values() if isinstance(v, (int, float)) and v > 0]
        return sum(vals) / len(vals) if vals else 10.0

    def _rechercher_master_par_objectif(self, objectif: str, profil: dict, top_k: int = 10) -> list:
        """
        Recherche des Masters pertinents pour l'objectif de carriere de l'etudiant.

        Scoring multi-criteres (score plus bas = meilleur) :
        1. Pertinence debouches : objectif de carriere vs debouches du Master
        2. Pertinence nom       : le nom du Master evoque le metier vise
        3. Bonus Paris          : Masters parisiens ponderes favorablement
        4. Notes de l'etudiant  : bonne moyenne -> acces Masters selectifs
        5. Budget               : "Public uniquement" -> penalise les prives
        6. Competences techniques : bonus si les competences matchent le contenu

        SANS contrainte geographique (l'etudiant bouge apres la Licence).
        """
        domaine = " ".join(profil.get("domaines_etudes_preferes", []))
        requete = f"Master {objectif} {domaine}"

        profil_national = {**profil, "contraintes_geographiques": ""}
        docs = self._rechercher_docs_bruts(requete, profil_national, over_fetch=200)
        docs = self._filtrer_par_type(docs, {"Master"})

        # Variables du profil pour le scoring
        objectif_lower = objectif.lower().strip()
        objectif_mots = set(objectif_lower.split())
        moyenne = self._moyenne_notes(profil)
        budget = profil.get("budget", "").lower()
        competences = [c.lower() for c in profil.get("competences_techniques", [])]

        def score_master(doc):
            meta = doc.metadata
            debouches_raw = meta.get("debouches_metiers", "")
            if isinstance(debouches_raw, str):
                debouches = debouches_raw.lower()
            else:
                debouches = " ".join(debouches_raw).lower() if debouches_raw else ""
            nom = meta.get("nom", "").lower()
            ville = (meta.get("ville", "") or "").lower()
            contenu = doc.page_content.lower()

            # --- 1. Score pertinence debouches (0-30) ---
            if objectif_lower in debouches:
                score_pert = 0              # Match exact du metier dans les debouches
            elif sum(1 for m in objectif_mots if m in debouches) >= 2:
                score_pert = 5              # Plusieurs mots matchent
            elif any(m in debouches for m in objectif_mots):
                score_pert = 10             # Au moins un mot
            elif any(m in nom for m in objectif_mots):
                score_pert = 15             # Match dans le nom du Master
            elif any(m in contenu for m in objectif_mots):
                score_pert = 20             # Match dans le contenu complet
            else:
                score_pert = 30             # Aucun match

            # --- 2. Bonus Paris (-3) ---
            # Masters parisiens = meilleur reseau, plus de debouches, reputation
            villes_paris = ["paris", "saclay", "nanterre", "creteil", "sceaux",
                            "orsay", "guyancourt", "villetaneuse", "saint-denis"]
            bonus_paris = -3 if any(v in ville for v in villes_paris) else 0

            # --- 3. Ajustement notes ---
            # Bonne moyenne : acces aux Masters selectifs sans penalite
            # Moyenne faible : on penalise pour proposer des Masters plus accessibles
            if moyenne >= 14:
                ajust_notes = 0
            elif moyenne >= 12:
                ajust_notes = 2
            else:
                ajust_notes = 5

            # --- 4. Budget : penaliser prive si "Public uniquement" ---
            budget_pen = 0
            if "public uniquement" in budget:
                modalite = (meta.get("modalite", "") or "").lower()
                if "priv" in modalite:
                    budget_pen = 50

            # --- 5. Bonus competences techniques (-1 par match, max -5) ---
            bonus_comp = 0
            for comp in competences:
                if comp in contenu or comp in nom:
                    bonus_comp -= 1
            bonus_comp = max(bonus_comp, -5)

            return score_pert + bonus_paris + ajust_notes + budget_pen + bonus_comp

        docs = sorted(docs, key=score_master)
        print(f"  Masters trouves : {len(docs)} | Top-3 scores : "
              f"{[score_master(d) for d in docs[:3]] if docs else 'aucun'}")
        return self._docs_vers_formations(docs, top_k)

    def _nettoyer_json(self, contenu: str) -> str:
        """Retire les balises markdown autour du JSON si presentes."""
        c = contenu.strip()
        if c.startswith("```json"):
            c = c[7:]
        if c.startswith("```"):
            c = c[3:]
        if c.endswith("```"):
            c = c[:-3]
        return c.strip()

    def generer_parcours(self, profil: dict, formation_choisie: dict) -> dict:
        """
        Genere un parcours COMPLET adapte au profil de l'etudiant.

        Approche RAG en 2 temps :
        T1 (avant LLM) : on detecte le cycle (universitaire / BUT), on predit les
                         niveaux, on recupere les vraies formations par niveau depuis
                         ChromaDB et on les injecte dans le prompt.
        T2 (apres LLM): on re-interroge ChromaDB etape par etape en utilisant la
                        VILLE de chaque etape comme centre de recherche, afin de
                        proposer des formations similaires dans la meme zone.
        """
        if not self._initialise:
            raise RuntimeError(
                "Le pipeline n'est pas initialise. "
                "Appelez pipeline.initialiser() d'abord."
            )

        profil_texte = formater_profil(profil)
        contexte = formation_choisie.get("contenu_complet", "")
        objectif = profil.get("objectif_professionnel", profil.get("objectif", ""))
        niveau_actuel = profil.get("niveau_actuel", "Terminale")

        # --- Detecter le cycle choisi ---
        cycle = self._detecter_cycle(formation_choisie)
        print(f"Cycle detecte : {cycle}")

        # --- T1 : RAG pre-prompt : formations reelles par niveau ---
        niveaux = self._predire_niveaux_etapes(niveau_actuel)
        print(f"Niveaux predits : {niveaux}")
        formations_context = self._construire_context_formations_par_niveau(
            niveaux, objectif, profil, top_k=5
        )

        # --- Construire le prompt avec cycle + niveau + formations reelles ---
        cycle_label = (
            "Cycle universitaire (Licence → L2 → L3 → Master)"
            if cycle == "universitaire"
            else "Cycle technologique (BUT 3 ans → Licence Pro ou insertion)"
        )
        domaine_actuel = ", ".join(profil.get("domaines_etudes_preferes", [])) or "Non specifie"
        prompt_final = PROMPT_PARCOURS.format(
            profil_etudiant=profil_texte,
            formation_cible=formation_choisie.get("nom", "Formation"),
            context=contexte,
            formations_disponibles=formations_context,
            cycle=cycle_label,
            niveau_actuel=niveau_actuel,
            domaine_actuel=domaine_actuel,
        )

        print("Generation du parcours (RAG + cycle + niveau)...\n")
        reponse = self.llm.invoke(prompt_final)
        contenu = reponse.content if hasattr(reponse, 'content') else str(reponse)

        try:
            parcours = json.loads(self._nettoyer_json(contenu))
            print("Parcours genere avec succes\n")
            # T2 : re-interroger la base — utiliser la ville de la formation choisie
            ville_formation = formation_choisie.get("ville", "").strip()
            if ville_formation:
                profil_enrichi = {**profil, "contraintes_geographiques": ville_formation}
            else:
                profil_enrichi = profil
            print(f"Enrichissement des alternatives (ville={ville_formation or profil.get('contraintes_geographiques','')}, cycle={cycle})...")
            parcours = self.enrichir_options_etapes(parcours, profil_enrichi, cycle=cycle)
            # Stocker le cycle dans le parcours pour l'interface
            parcours["_cycle"] = cycle
            print("Enrichissement termine\n")
            return parcours
        except json.JSONDecodeError:
            print("Le LLM n'a pas retourne du JSON valide\n")
            return {
                "resume": contenu,
                "etapes": [],
                "prerequis": {},
                "defis": [],
                "alternatives": [],
                "conseils_personnalises": [],
                "_raw_response": True,
                "_cycle": cycle,
            }

    def generer_suite_parcours(
        self,
        profil: dict,
        choix_precedents: list,
        formation_cible: str,
    ) -> dict:
        """
        Regenere un parcours COMPLET et PERSONNALISE apres un choix de l'etudiant.

        Differemment de l'ancienne version (qui ne regenerait que les etapes suivantes),
        cette version genere un nouveau parcours complet adapte a TOUS les choix faits.
        Le cycle est detecte depuis les choix precedents (si un BUT a ete choisi, le
        parcours continue en cycle BUT).
        """
        if not self._initialise:
            raise RuntimeError("Le pipeline n'est pas initialise.")

        profil_texte = formater_profil(profil)
        choix_texte = json.dumps(choix_precedents, ensure_ascii=False, indent=2)
        objectif = profil.get("objectif_professionnel", profil.get("objectif", ""))

        # Detecter le cycle depuis les choix precedents
        dernier_choix = choix_precedents[-1] if choix_precedents else {}
        cycle = self._detecter_cycle({}, choix_precedents)
        print(f"Cycle detecte depuis les choix : {cycle}")

        # Niveau atteint = dernier choix fait
        niveau_atteint = dernier_choix.get("choix", "")
        ville_actuelle = dernier_choix.get("ville", "")

        # Construire un profil mis a jour avec la ville du dernier choix
        profil_mis_a_jour = {
            **profil,
            "contraintes_geographiques": ville_actuelle or profil.get("contraintes_geographiques", ""),
        }

        # Niveaux restants a partir du dernier choix
        niveaux_restants = self._predire_niveaux_etapes(niveau_atteint)
        formations_context = self._construire_context_formations_par_niveau(
            niveaux_restants, objectif, profil_mis_a_jour, top_k=5
        )

        cycle_label = (
            "Cycle universitaire (Licence → Master)"
            if cycle == "universitaire"
            else "Cycle technologique (BUT → Licence Pro ou insertion)"
        )

        domaine_actuel = ", ".join(profil.get("domaines_etudes_preferes", [])) or "Non specifie"
        prompt_final = PROMPT_SUITE_PARCOURS.format(
            profil_etudiant=profil_texte,
            choix_precedents=choix_texte,
            formation_cible=formation_cible,
            formations_disponibles=formations_context,
            cycle=cycle_label,
            niveau_atteint=niveau_atteint,
            domaine_actuel=domaine_actuel,
        )

        print(f"Re-personnalisation depuis : {niveau_atteint} | cycle={cycle}")
        reponse = self.llm.invoke(prompt_final)
        contenu = reponse.content if hasattr(reponse, 'content') else str(reponse)

        try:
            result = json.loads(self._nettoyer_json(contenu))
            print("Parcours re-personnalise genere\n")
            result = self.enrichir_options_etapes(
                result, profil_mis_a_jour, cycle=cycle
            )
            result["_cycle"] = cycle
            return result
        except json.JSONDecodeError:
            print("Erreur JSON dans la re-personnalisation\n")
            return {"etapes": [], "_cycle": cycle}


# Test rapide
if __name__ == "__main__":
    pipeline = PipelineRAG()
    pipeline.initialiser(rebuild=True)

    # Profil de test avec les 14 variables
    profil_test = {
        "niveau_actuel": "Licence 3 Informatique",
        "objectif_professionnel": "Devenir Data Scientist",
        "matieres_fortes": ["Programmation", "Mathematiques", "Statistiques"],
        "matieres_faibles": ["Anglais"],
        "notes_par_matiere": {"Maths": 16, "Informatique": 15, "Anglais": 10},
        "competences_techniques": ["Python", "SQL", "Machine Learning"],
        "qualites_personnelles": ["Rigoureux", "Curieux", "Travail en equipe"],
        "langues": [{"langue": "Francais", "niveau": "C2"}, {"langue": "Anglais", "niveau": "B1"}],
        "experiences_stages": ["Stage 2 mois developpement web"],
        "domaines_etudes_preferes": ["Data Science", "Intelligence Artificielle"],
        "centres_interet": ["IA", "Analyse de donnees", "Environnement"],
        "type_formation_prefere": "Formation initiale",
        "contraintes_geographiques": "Sud de la France",
        "budget": "Public uniquement",
    }

    parcours = pipeline.generer_parcours(profil_test)
    print(json.dumps(parcours, indent=2, ensure_ascii=False))
