import streamlit as st
import requests
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
TMDB_API_KEY    = st.secrets.get("TMDB_API_KEY", "620b231f411093a0f74352c5530d184a")
GEMINI_API_KEY  = st.secrets.get("GEMINI_API_KEY", "")
VU_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "films_vus.json")
AVOIR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "films_avoir.json")

st.set_page_config(
    page_title="Cinémathèque Mr Marc",
    layout="wide",
    page_icon="🎬",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CSS — THÈME CINÉMATHÈQUE NOIR / OR
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #080810 !important; color: #e8e0d0 !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1a 0%, #080810 100%) !important;
    border-right: 1px solid #1e1c2a !important;
}
[data-testid="stSidebar"] * { color: #e8e0d0 !important; }
h1,h2,h3 { font-family: 'Playfair Display', serif !important; }
p,span,div,label,button { font-family: 'DM Sans', sans-serif !important; }

/* ── Hero ── */
.hero-title {
    font-family: 'Playfair Display', serif; font-size: 3.4rem; font-weight: 700;
    background: linear-gradient(135deg, #d4af37 0%, #f5e67a 45%, #b8890a 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.1; margin-bottom: .2rem;
}
.hero-sub {
    font-size: .85rem; color: #4a4438; letter-spacing: 4px;
    text-transform: uppercase; margin-bottom: 2rem;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: .85rem !important; letter-spacing: 1.5px !important;
    text-transform: uppercase !important; color: #7a7060 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #d4af37 !important; border-bottom: 2px solid #d4af37 !important;
}

/* ── Carte film ── */
.film-card {
    background: linear-gradient(160deg, #12111e, #181626);
    border: 1px solid #22203a; border-radius: 12px; overflow: hidden;
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
    height: 100%;
}
.film-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 24px 48px rgba(0,0,0,.7), 0 0 0 1px #d4af37;
    border-color: #d4af37;
}
.film-poster { width:100%; aspect-ratio:2/3; object-fit:cover; display:block; }
.film-poster-ph {
    width:100%; aspect-ratio:2/3;
    background: linear-gradient(135deg,#181626,#0d0d1a);
    display:flex; align-items:center; justify-content:center;
    font-size:3rem; color:#22203a;
}
.film-info { padding:14px; }
.film-title {
    font-family:'Playfair Display',serif; font-size:1rem; font-weight:700;
    color:#e8e0d0; margin:0 0 8px; line-height:1.3;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}
.film-meta { display:flex; align-items:center; gap:8px; margin-bottom:10px; flex-wrap:wrap; }
.note-badge {
    background: linear-gradient(135deg,#d4af37,#b8890a);
    color:#080810; font-weight:700; font-size:.78rem; padding:3px 9px; border-radius:20px;
}
.annee-badge { color:#7a7060; font-size:.78rem; }
.platform-chip {
    display:inline-block; background:rgba(212,175,55,.1); border:1px solid rgba(212,175,55,.25);
    color:#d4af37; font-size:.68rem; padding:2px 8px; border-radius:20px;
    margin:2px 2px 0 0; white-space:nowrap;
}
.platform-chips { flex-wrap:wrap; display:flex; margin-top:4px; }

/* ── Search bar ── */
.search-wrap {
    background: linear-gradient(135deg, #12111e, #161526);
    border: 1px solid #2a2540; border-radius: 14px;
    padding: 20px 24px; margin-bottom: 24px;
}
.search-title {
    font-family: 'Playfair Display', serif; font-size: 1.1rem;
    color: #d4af37; margin-bottom: 10px;
}

/* ── Résultat recherche par nom ── */
.search-result-card {
    background: linear-gradient(145deg, #12111e, #181626);
    border: 1px solid #22203a; border-radius: 12px;
    padding: 16px; margin-bottom: 12px;
    display: flex; gap: 16px; align-items: flex-start;
    transition: border-color .2s;
}
.search-result-card:hover { border-color: #3a3428; }
.search-result-poster {
    width: 60px; min-width: 60px; border-radius: 6px; object-fit: cover;
}
.search-result-ph {
    width: 60px; min-width: 60px; height: 90px; border-radius: 6px;
    background: #161524; display: flex; align-items: center;
    justify-content: center; font-size: 1.5rem; color: #22203a;
}
.search-result-info { flex: 1; }
.search-result-title {
    font-family: 'Playfair Display', serif; font-size: 1rem;
    color: #e8e0d0; margin: 0 0 6px;
}

/* ── Détail film ── */
.detail-wrap {
    background: linear-gradient(145deg,#12111e,#0f0e1a);
    border:1px solid #22203a; border-radius:16px; padding:28px; margin-bottom:20px;
}
.detail-title { font-family:'Playfair Display',serif; font-size:1.9rem; color:#e8e0d0; margin-bottom:4px; }
.detail-tagline { color:#6a6050; font-style:italic; font-size:.95rem; margin-bottom:16px; }
.synopsis { color:#a8a098; line-height:1.8; font-size:.94rem; }
.cast-chip {
    display:inline-block; background:#161524; border:1px solid #22203a;
    color:#c0b8a8; font-size:.75rem; padding:4px 10px; border-radius:20px; margin:3px 3px 0 0;
}
.section-lbl {
    font-size:.7rem; text-transform:uppercase; letter-spacing:2.5px;
    color:#3a3428; margin:16px 0 8px;
}

/* ── À VOIR liste ── */
.avoir-card {
    background: linear-gradient(145deg, #12111e, #181626);
    border: 1px solid #22203a; border-radius: 12px; overflow: hidden;
    transition: transform .2s, border-color .2s;
}
.avoir-card:hover {
    transform: translateY(-4px); border-color: #3a3428;
}

/* ── Humeur / AI ── */
.ai-response {
    background: linear-gradient(145deg,#12111e,#161424);
    border-left: 3px solid #d4af37; border-radius:0 12px 12px 0;
    padding:20px 24px; margin-top:16px;
    font-size:.95rem; color:#c0b8a8; line-height:1.8;
}

/* ── Journal ── */
.journal-entry {
    background:#12111e; border:1px solid #22203a; border-radius:10px;
    padding:16px; margin-bottom:12px; transition: border-color .2s;
}
.journal-entry:hover { border-color: #3a3428; }
.journal-film { font-family:'Playfair Display',serif; font-size:1rem; color:#e8e0d0; }
.journal-date { font-size:.75rem; color:#4a4438; margin-top:2px; }
.journal-note { color:#d4af37; font-size:.85rem; margin-top:6px; }
.journal-comment { color:#8a8278; font-size:.85rem; margin-top:6px; font-style:italic; }

/* ── Résultats ── */
.result-bar {
    font-size:.82rem; color:#7a7060; margin-bottom:1.5rem;
    padding-bottom:.8rem; border-bottom:1px solid #1e1c2a;
}
.result-bar strong { color:#d4af37; }

/* ── Inputs texte ── */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background:#12111e !important; border:1px solid #22203a !important;
    color:#e8e0d0 !important; border-radius:8px !important;
}
[data-testid="stSelectbox"] > div > div {
    background:#12111e !important; border:1px solid #22203a !important;
    border-radius:8px !important; color:#e8e0d0 !important;
}
.stSlider [data-testid="stSliderThumb"]     { background:#d4af37 !important; }
.stSlider [data-testid="stSliderTrackFill"] { background:#d4af37 !important; }
.stNumberInput input { background:#12111e !important; border:1px solid #22203a !important; color:#e8e0d0 !important; }

/* ── Sidebar labels ── */
.sb-lbl { font-size:.62rem; text-transform:uppercase; letter-spacing:1.5px; color:#3a3428; margin:6px 0 3px; }

/* Bouton play sous jaquette - discret */
div[data-testid="stMain"] div.stButton > button {
    background: rgba(212,175,55,0.15) !important;
    border: 1px solid rgba(212,175,55,0.3) !important;
    color: #d4af37 !important; font-size: .75rem !important;
    padding: 4px !important; min-height: 28px !important;
    width: 100% !important; border-radius: 0 0 8px 8px !important;
    margin-top: -4px !important;
}
div[data-testid="stMain"] div.stButton > button:hover {
    background: rgba(212,175,55,0.35) !important;
    cursor: pointer !important;
}

/* Boutons genre */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: #12111e !important; border: 1px solid #2a2535 !important;
    color: #7a7060 !important; font-size: .62rem !important;
    padding: 1px 2px !important; min-height: 22px !important; line-height: 1 !important;
    border-radius: 4px !important; white-space: nowrap !important;
    overflow: hidden !important; text-overflow: ellipsis !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg,#d4af37,#b8890a) !important;
    border: none !important; color: #080810 !important;
    font-size: .62rem !important; font-weight: 700 !important;
    padding: 1px 2px !important; min-height: 22px !important; line-height: 1 !important;
    border-radius: 4px !important; white-space: nowrap !important;
    overflow: hidden !important; text-overflow: ellipsis !important;
}
[data-testid="stCheckbox"] label { font-size:.82rem !important; color:#c0b8a8 !important; }
[data-testid="stCheckbox"] { margin-bottom:-8px; }

#MainMenu, footer, [data-testid="stDecoration"] { display:none !important; }
[data-testid="stSidebarHeader"] { display:none !important; }
[data-testid="stSidebarCollapseButton"] { display:none !important; }
section[data-testid="stSidebar"] { padding-top: 0.5rem !important; }
section[data-testid="stSidebar"] > div { padding-top: 0.3rem !important; }
[data-testid="stSidebar"] .stMarkdown p { margin: 0 !important; padding: 0 !important; }
[data-testid="stSidebar"] .element-container { margin-bottom: 0 !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] { gap: 0 !important; }
[data-testid="stSidebar"] hr { margin: 4px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DONNÉES
# ─────────────────────────────────────────────
MES_PLATEFORMES = {
    "Netflix": 8, "Canal+": 381, "Disney+": 337, "Amazon Prime": 119,
    "Max": 1899, "Arte": 234, "France TV": 312, "MyTF1 Max": 1870,
    "6play Max": 1866, "OCS": 56, "UniversCiné": 310,
}
GENRES = {
    "Action": 28, "Animation": 16, "Aventure": 12, "Comédie": 35,
    "Crime": 80, "Documentaire": 99, "Drame": 18, "Familial": 10751,
    "Fantastique": 14, "Guerre": 10752, "Histoire": 36, "Horreur": 27,
    "Musique": 10402, "Mystère": 9648, "Romance": 10749,
    "Science-Fiction": 878, "Thriller": 53, "Western": 37,
}
COLLECTIONS = {
    "🌟 Standard": "none", "🏆 Oscars & Primés": "awards",
    "🇫🇷 Cinéma Français": "french", "🎞️ Noir & Blanc": "bw",
    "🕰️ Classiques (< 1975)": "classics", "💎 Pépites cachées": "hidden_gems",
}
TRIS = {
    "🔥 Popularité": "popularity.desc",
    "⭐ Meilleures notes": "vote_average.desc",
    "🆕 Les plus récents": "primary_release_date.desc",
    "🕰️ Les plus anciens": "primary_release_date.asc",
}
HUMEURS = [
    "Décris ce que tu as envie de ressentir ce soir…",
    "Un film qui me tient en haleine sans me stresser",
    "Quelque chose de profond et émouvant",
    "Une comédie légère pour décompresser",
    "Un chef-d'œuvre que je n'ai pas encore vu",
    "Un film d'aventure dépaysant",
    "Un thriller psychologique intelligent",
    "Un film français du patrimoine",
]

# ─────────────────────────────────────────────
#  FILMS VUS — stockage JSON local
# ─────────────────────────────────────────────
def vu_charger():
    try:
        with open(VU_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def vu_sauver(data):
    try:
        with open(VU_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def vu_ajouter(film_id, titre, annee):
    data = vu_charger()
    data[str(film_id)] = {"titre": titre, "annee": annee, "date": datetime.now().strftime("%d/%m/%Y")}
    return vu_sauver(data)

def vu_retirer(film_id):
    data = vu_charger()
    data.pop(str(film_id), None)
    return vu_sauver(data)

def vu_ids():
    return set(vu_charger().keys())

# ─────────────────────────────────────────────
#  FILMS À VOIR — stockage JSON local
# ─────────────────────────────────────────────
def avoir_charger():
    try:
        with open(AVOIR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def avoir_sauver(data):
    try:
        with open(AVOIR_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def avoir_ajouter(film_id, titre, annee):
    data = avoir_charger()
    data[str(film_id)] = {"titre": titre, "annee": annee, "date": datetime.now().strftime("%d/%m/%Y")}
    return avoir_sauver(data)

def avoir_retirer(film_id):
    data = avoir_charger()
    data.pop(str(film_id), None)
    return avoir_sauver(data)

def avoir_ids():
    return set(avoir_charger().keys())

# ─────────────────────────────────────────────
#  API TMDB
# ─────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def rechercher_films(genre_ids, provider_id, col_key, annee_min, note_mini, tri, page=1):
    ids_str = provider_id if provider_id else "|".join(str(v) for v in MES_PLATEFORMES.values())
    params = {
        "api_key": TMDB_API_KEY, "language": "fr-FR",
        "watch_region": "FR", "with_watch_monetization_types": "flatrate",
        "with_watch_providers": ids_str, "vote_average.gte": note_mini,
        "vote_count.gte": 80, "sort_by": tri, "page": page,
    }
    if col_key == "awards":   params["vote_count.gte"] = 1000
    elif col_key == "french": params["with_original_language"] = "fr"
    elif col_key == "bw":     params["with_keywords"] = "2343"
    elif col_key == "classics": params["primary_release_date.lte"] = "1975-01-01"
    elif col_key == "hidden_gems": params["vote_count.gte"] = 50; params["vote_count.lte"] = 500
    if genre_ids: params["with_genres"] = genre_ids
    if annee_min and col_key != "classics":
        params["primary_release_date.gte"] = f"{annee_min}-01-01"
    try:
        r = requests.get("https://api.themoviedb.org/3/discover/movie", params=params, timeout=6)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def rechercher_par_nom(query: str):
    """Recherche TMDB par titre — retourne les 10 premiers résultats."""
    if not query or len(query.strip()) < 2:
        return []
    try:
        params = {
            "api_key": TMDB_API_KEY,
            "language": "fr-FR",
            "query": query.strip(),
            "include_adult": False,
            "page": 1,
        }
        r = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=6)
        r.raise_for_status()
        return r.json().get("results", [])[:10]
    except Exception:
        return []

JW_NOMS = {
    "Netflix": "Netflix",
    "Amazon Prime Video": "Amazon Prime",
    "Amazon Prime Video with Ads": "Amazon Prime",
    "Disney Plus": "Disney+",
    "Disney+": "Disney+",
    "Canal+": "Canal+",
    "Max": "Max",
    "HBO Max": "Max",
    "Apple TV Plus": "Apple TV+",
    "Apple TV+": "Apple TV+",
    "Paramount Plus": "Paramount+",
    "Paramount+": "Paramount+",
    "Ciné+": "CINÉ+",
    "CINÉ+": "CINÉ+",
    "Arte": "Arte",
    "France Télévisions": "France TV",
    "France.tv": "France TV",
    "MyTF1": "MyTF1 Max",
    "TF1+": "MyTF1 Max",
    "6play": "6play Max",
    "M6+": "6play Max",
    "OCS": "OCS",
    "UniversCiné": "UniversCiné",
    "Universciné": "UniversCiné",
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_plateformes_tmdb(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
        data = requests.get(url, timeout=4).json()
        flat = data.get("results", {}).get("FR", {}).get("flatrate", [])
        return [p["provider_name"] for p in flat if p["provider_name"] in MES_PLATEFORMES]
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_plateformes_justwatch(titre: str, annee: str) -> list:
    try:
        from simplejustwatchapi.justwatch import search
        resultats = search(titre, "FR", "fr", 3, True)
        if not resultats:
            return []
        offres = []
        for item in resultats[:5]:
            item_titre = (item.title or "").lower()
            if titre.lower()[:6] in item_titre or item_titre[:6] in titre.lower():
                for offer in (item.offers or []):
                    if offer.monetization_type == "FLATRATE":
                        nom_jw = offer.package.name if offer.package else ""
                        nom_app = JW_NOMS.get(nom_jw)
                        if nom_app and nom_app not in offres:
                            offres.append(nom_app)
                if offres:
                    return offres
        return []
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_plateformes(movie_id, titre="", annee=""):
    tmdb = get_plateformes_tmdb(movie_id)
    jw   = get_plateformes_justwatch(titre, annee) if titre else []
    union = list(dict.fromkeys(tmdb + [p for p in jw if p not in tmdb]))
    return [p for p in union if p in MES_PLATEFORMES]

@st.cache_data(ttl=3600, show_spinner=False)
def get_details(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=fr-FR&append_to_response=credits,videos,keywords"
        return requests.get(url, timeout=5).json()
    except Exception:
        return {}

def enrichir_parallel(films_brut, max_films=20):
    def _fetch(film):
        titre = film.get("title", "")
        annee = film.get("release_date", "")[:4]
        offres = get_plateformes(film["id"], titre, annee)
        if offres:
            film["offres"] = offres
            return film
        return None

    films_ok = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_fetch, f): f for f in films_brut[:40]}
        for fut in as_completed(futures):
            result = fut.result()
            if result:
                films_ok.append(result)
            if len(films_ok) >= max_films:
                break
    return films_ok

# ─────────────────────────────────────────────
#  GEMINI — RECOMMANDATION PAR HUMEUR
# ─────────────────────────────────────────────
def recommander_par_humeur(humeur: str, films: list[dict]) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ Clé API Gemini non configurée dans les secrets Streamlit."
    if not films:
        return "Aucun film disponible pour faire une recommandation."

    catalogue = "\n".join(
        f"- {f['title']} ({f.get('release_date','')[:4]}) — Note: {f.get('vote_average',0):.1f}/10 "
        f"| Plateformes: {', '.join(f.get('offres',[]))}"
        for f in films[:20]
    )

    prompt = f"""Tu es le programmateur d'une cinémathèque de prestige parisienne.
Mr Marc exprime cette envie ce soir : « {humeur} »

Voici les films disponibles sur ses plateformes ce soir :
{catalogue}

Sélectionne 3 films de cette liste qui correspondent parfaitement à son envie.
Pour chacun, donne :
1. Le titre exact (tel qu'il apparaît dans la liste)
2. Une phrase d'accroche cinéphile (jamais banale, évocatrice)
3. Pourquoi ce film répond précisément à son envie ce soir

Commence directement, pas d'introduction générique. Ton élégant et cultivé, comme les Cahiers du Cinéma."""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Erreur Gemini : {e}"

# ─────────────────────────────────────────────
#  COMPOSANTS UI
# ─────────────────────────────────────────────
def carte_html(film):
    titre = film.get("title", "Inconnu")
    note  = film.get("vote_average", 0)
    annee = film.get("release_date", "")[:4] or "—"
    offres = film.get("offres", [])
    poster = film.get("poster_path")
    img = (f'<img class="film-poster" src="https://image.tmdb.org/t/p/w400{poster}" alt="{titre}" loading="lazy">'
           if poster else '<div class="film-poster-ph">🎬</div>')
    chips = "".join(f'<span class="platform-chip">{o}</span>' for o in offres)
    return f"""
    <div class="film-card">
        {img}
        <div class="film-info">
            <p class="film-title">{titre}</p>
            <div class="film-meta">
                <span class="note-badge">★ {note:.1f}</span>
                <span class="annee-badge">{annee}</span>
            </div>
            <div class="platform-chips">{chips}</div>
        </div>
    </div>"""

def afficher_detail(film_id):
    d = get_details(film_id)
    if not d:
        st.warning("Impossible de charger les détails.")
        return

    col_img, col_txt = st.columns([1, 2.5], gap="large")

    with col_img:
        if d.get("poster_path"):
            st.image(f"https://image.tmdb.org/t/p/w400{d['poster_path']}", use_container_width=True)

    with col_txt:
        st.markdown(f'<p class="detail-title">{d.get("title","")}</p>', unsafe_allow_html=True)
        if d.get("tagline"):
            st.markdown(f'<p class="detail-tagline">« {d["tagline"]} »</p>', unsafe_allow_html=True)

        annee  = d.get("release_date","")[:4] or "—"
        duree  = d.get("runtime", 0)
        note   = d.get("vote_average", 0)
        votes  = d.get("vote_count", 0)
        duree_fmt = f"{duree//60}h{duree%60:02d}" if duree else "—"
        st.markdown(
            f'<div class="film-meta">'
            f'<span class="note-badge">★ {note:.1f}</span>'
            f'<span class="annee-badge">{annee}</span>'
            f'<span class="annee-badge">⏱ {duree_fmt}</span>'
            f'<span class="annee-badge">👥 {votes:,} votes</span>'
            f'</div>', unsafe_allow_html=True)

        genres = [g["name"] for g in d.get("genres", [])]
        if genres:
            st.markdown('<p class="section-lbl">Genres</p>', unsafe_allow_html=True)
            st.markdown("".join(f'<span class="cast-chip">{g}</span>' for g in genres), unsafe_allow_html=True)

        if d.get("overview"):
            st.markdown('<p class="section-lbl">Synopsis</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="synopsis">{d["overview"]}</p>', unsafe_allow_html=True)

        crew  = d.get("credits", {}).get("crew", [])
        reals = [c["name"] for c in crew if c.get("job") == "Director"]
        if reals:
            st.markdown('<p class="section-lbl">Réalisateur</p>', unsafe_allow_html=True)
            st.markdown("".join(f'<span class="cast-chip">🎬 {r}</span>' for r in reals[:2]), unsafe_allow_html=True)

        cast = d.get("credits", {}).get("cast", [])[:6]
        if cast:
            st.markdown('<p class="section-lbl">Avec</p>', unsafe_allow_html=True)
            st.markdown("".join(f'<span class="cast-chip">{a["name"]}</span>' for a in cast), unsafe_allow_html=True)

        videos = d.get("videos", {}).get("results", [])
        trailer = next((v for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)
        if trailer:
            st.markdown('<p class="section-lbl">Bande-annonce</p>', unsafe_allow_html=True)
            st.video(f"https://www.youtube.com/watch?v={trailer['key']}")

        # Boutons VU + À VOIR
        vus = vu_ids()
        avoirs = avoir_ids()
        deja_vu = str(film_id) in vus
        deja_avoir = str(film_id) in avoirs
        st.markdown('<p class="section-lbl">Mon suivi</p>', unsafe_allow_html=True)
        col_vu, col_avoir = st.columns(2)
        with col_vu:
            if deja_vu:
                st.success(f"✅ Vu le {vu_charger()[str(film_id)].get('date','')}")
                if st.button("↩️ Retirer des vus", key=f"retirer_{film_id}"):
                    vu_retirer(film_id)
                    st.rerun()
            else:
                if st.button("👁 Marquer comme VU", key=f"vu_{film_id}", use_container_width=True):
                    vu_ajouter(film_id, d.get("title",""), annee)
                    avoir_retirer(film_id)
                    st.rerun()
        with col_avoir:
            if deja_avoir:
                st.info(f"🔖 Ajouté le {avoir_charger()[str(film_id)].get('date','')}")
                if st.button("↩️ Retirer de À voir", key=f"retirer_avoir_{film_id}"):
                    avoir_retirer(film_id)
                    st.rerun()
            elif not deja_vu:
                if st.button("🔖 À VOIR", key=f"avoir_{film_id}", use_container_width=True):
                    avoir_ajouter(film_id, d.get("title",""), annee)
                    st.rerun()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-family:\'Playfair Display\',serif;font-size:1.3rem;'
        'font-weight:700;color:#d4af37;margin-bottom:0;">🎬 Cinémathèque</p>'
        '<p style="font-size:.7rem;color:#3a3428;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:1rem;">Mr Marc</p>',
        unsafe_allow_html=True)
    st.divider()

    st.markdown('<p class="sb-lbl">Genres</p>', unsafe_allow_html=True)
    if "genres_choisis" not in st.session_state:
        st.session_state.genres_choisis = []

    genre_list = list(GENRES.keys())
    cols = st.columns(2)
    for i, g in enumerate(genre_list):
        with cols[i % 2]:
            actif = g in st.session_state.genres_choisis
            if st.button(g, key=f"g_{g}", use_container_width=True,
                        type="primary" if actif else "secondary"):
                if actif:
                    st.session_state.genres_choisis.remove(g)
                else:
                    st.session_state.genres_choisis.append(g)
                st.rerun()

    genres_choisis = st.session_state.genres_choisis
    genre_ids = ",".join(str(GENRES[g]) for g in genres_choisis) if genres_choisis else None

    st.markdown('<p class="sb-lbl">Collection</p>', unsafe_allow_html=True)
    choix_c = st.selectbox("Collection", list(COLLECTIONS.keys()), label_visibility="collapsed")
    col_key = COLLECTIONS[choix_c]

    st.markdown('<p class="sb-lbl">Trier par</p>', unsafe_allow_html=True)
    idx_note = list(TRIS.keys()).index("⭐ Meilleures notes")
    choix_tri = st.selectbox("Trier par", list(TRIS.keys()), index=idx_note, label_visibility="collapsed")
    tri_val = TRIS[choix_tri]

    st.markdown('<p class="sb-lbl">Année minimum</p>', unsafe_allow_html=True)
    annee_min = st.slider("Année minimum", 1930, 2025, 2010, label_visibility="collapsed")

    note_mini = 8.0

    lancer = st.button("🚀 Lancer la recherche", use_container_width=True, key="btn_lancer")

    masquer_vus = st.toggle("🙈 Masquer les films déjà vus", value=False)

    st.divider()
    st.markdown('<p class="sb-lbl">📺 Mes plateformes</p>', unsafe_allow_html=True)
    plat_coches = st.multiselect(
        "Plateformes",
        options=list(MES_PLATEFORMES.keys()),
        default=list(MES_PLATEFORMES.keys()),
        label_visibility="collapsed",
        placeholder="Choisir des plateformes…"
    )
    if not plat_coches or len(plat_coches) == len(MES_PLATEFORMES):
        provider_id = None
    else:
        provider_id = "|".join(str(MES_PLATEFORMES[p]) for p in plat_coches)

    st.markdown('<p style="font-size:.68rem;color:#2a2418;text-align:center;margin-top:1rem;">Données · TMDB API</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ÉTAT SESSION
# ─────────────────────────────────────────────
for key in ["films_ok", "film_detail", "search_query", "search_results", "search_detail"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ("films_ok", "search_results") else None

# ─────────────────────────────────────────────
#  ZONE PRINCIPALE
# ─────────────────────────────────────────────
st.markdown('<p class="hero-title">La Cinémathèque</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Sélection personnelle · Mr Marc</p>', unsafe_allow_html=True)

tab_recherche, tab_nom, tab_humeur, tab_avoir, tab_journal = st.tabs([
    "🔍  Recherche",
    "🔎  Chercher un film",
    "🎭  Humeur du soir",
    "🔖  À Voir",
    "📖  Films Vus",
])

# ══════════════════════════════════════════════
#  TAB 1 — RECHERCHE PAR CRITÈRES
# ══════════════════════════════════════════════
with tab_recherche:

    if lancer:
        with st.spinner("Double vérification TMDB + JustWatch en cours…"):
            brut  = rechercher_films(genre_ids, provider_id, col_key, annee_min, note_mini, tri_val, page=1)
            brut += rechercher_films(genre_ids, provider_id, col_key, annee_min, note_mini, tri_val, page=2)
            seen, brut_u = set(), []
            for f in brut:
                if f["id"] not in seen:
                    seen.add(f["id"]); brut_u.append(f)
            st.session_state.films_ok = enrichir_parallel(brut_u, max_films=20)
            st.session_state.film_detail = None

    films = st.session_state.films_ok

    if not lancer and not films:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#12111e,#1a1826);border:1px solid #22203a;
             border-radius:16px;padding:3rem;text-align:center;max-width:560px;margin:4rem auto;">
            <div style="font-size:3.5rem;margin-bottom:1rem;">🎥</div>
            <p style="font-family:'Playfair Display',serif;font-size:1.4rem;color:#e8e0d0;margin-bottom:.8rem;">
                Bonsoir Mr Marc</p>
            <p style="color:#5a5048;line-height:1.8;font-size:.95rem;">
                Affinez vos critères dans le panneau de gauche<br>et cliquez sur
                <strong style="color:#d4af37;">Lancer la recherche</strong>.</p>
        </div>""", unsafe_allow_html=True)

    elif films:
        vus = vu_ids()
        films_affiches = [f for f in films if str(f["id"]) not in vus] if masquer_vus else films
        nb = len(films_affiches)
        st.markdown(
            f'<p class="result-bar"><strong>{nb} film{"s" if nb>1 else ""}</strong> — '
            f'{", ".join(genres_choisis) if genres_choisis else "Tous genres"} · {choix_c} · depuis {annee_min} · note ≥ {note_mini} · {choix_tri}</p>',
            unsafe_allow_html=True)

        if st.session_state.film_detail:
            fid = st.session_state.film_detail
            with st.container():
                st.markdown('<div class="detail-wrap">', unsafe_allow_html=True)
                if st.button("← Retour à la sélection"):
                    st.session_state.film_detail = None
                    st.rerun()
                afficher_detail(fid)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            for i in range(0, len(films_affiches), 4):
                cols = st.columns(4, gap="medium")
                for j, film in enumerate(films_affiches[i:i+4]):
                    with cols[j]:
                        fid = film['id']
                        st.markdown(carte_html(film), unsafe_allow_html=True)
                        if st.button("ℹ️ Détails", key=f"btn_{fid}", use_container_width=True):
                            st.session_state.film_detail = fid
                            st.rerun()

    elif lancer:
        st.markdown("""
        <div style="background:#12111e;border:1px solid #22203a;border-radius:16px;
             padding:2.5rem;text-align:center;max-width:480px;margin:3rem auto;">
            <div style="font-size:2.5rem;margin-bottom:.8rem;">🔍</div>
            <p style="font-family:'Playfair Display',serif;color:#e8e0d0;">Aucun résultat</p>
            <p style="color:#4a4438;font-size:.9rem;">Élargissez vos critères — baissez la note, changez de genre ou d'année.</p>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 2 — RECHERCHE PAR NOM
# ══════════════════════════════════════════════
with tab_nom:
    st.markdown('<p style="font-family:\'Playfair Display\',serif;font-size:1.5rem;color:#e8e0d0;margin-bottom:.4rem;">Rechercher un film par titre</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#4a4438;font-size:.9rem;margin-bottom:1.2rem;">Tapez un titre en français ou en anglais — TMDB cherche dans sa base mondiale.</p>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        query = st.text_input(
            "Titre du film",
            placeholder="Ex : Parasite, Le Fabuleux Destin…, Inception…",
            label_visibility="collapsed",
            key="search_input"
        )
    with col_btn:
        chercher = st.button("🔍 Chercher", use_container_width=True)

    # Lancement recherche
    if chercher and query:
        with st.spinner("Recherche en cours…"):
            st.session_state.search_results = rechercher_par_nom(query)
            st.session_state.search_query = query
            st.session_state.search_detail = None

    # Affichage du détail d'un résultat
    if st.session_state.search_detail:
        fid = st.session_state.search_detail
        st.markdown('<div class="detail-wrap">', unsafe_allow_html=True)
        if st.button("← Retour aux résultats", key="back_search"):
            st.session_state.search_detail = None
            st.rerun()
        afficher_detail(fid)
        st.markdown('</div>', unsafe_allow_html=True)

    # Liste des résultats
    elif st.session_state.search_results:
        resultats = st.session_state.search_results
        q = st.session_state.search_query or ""
        st.markdown(
            f'<p class="result-bar"><strong>{len(resultats)} résultat{"s" if len(resultats)>1 else ""}</strong> pour « {q} »</p>',
            unsafe_allow_html=True)

        vus = vu_ids()
        avoirs = avoir_ids()

        for film in resultats:
            fid   = film["id"]
            titre = film.get("title", "Inconnu")
            annee = film.get("release_date", "")[:4] or "—"
            note  = film.get("vote_average", 0)
            poster = film.get("poster_path")
            overview = film.get("overview", "Pas de synopsis disponible.")[:160] + "…"

            deja_vu    = str(fid) in vus
            deja_avoir = str(fid) in avoirs

            img_html = (
                f'<img class="search-result-poster" src="https://image.tmdb.org/t/p/w185{poster}" alt="{titre}">'
                if poster else '<div class="search-result-ph">🎬</div>'
            )

            vu_label    = "✅ Vu"    if deja_vu    else ""
            avoir_label = "🔖 À voir" if deja_avoir else ""
            badges = "".join(
                f'<span class="platform-chip">{b}</span>'
                for b in [vu_label, avoir_label] if b
            )

            st.markdown(f"""
            <div class="search-result-card">
                {img_html}
                <div class="search-result-info">
                    <p class="search-result-title">{titre}</p>
                    <div class="film-meta">
                        <span class="note-badge">★ {note:.1f}</span>
                        <span class="annee-badge">{annee}</span>
                        {badges}
                    </div>
                    <p style="color:#6a6060;font-size:.82rem;line-height:1.5;margin:6px 0 0;">{overview}</p>
                </div>
            </div>""", unsafe_allow_html=True)

            # Actions inline sous chaque résultat
            col_det, col_vu_btn, col_av_btn = st.columns([2, 1, 1])
            with col_det:
                if st.button("ℹ️ Voir les détails", key=f"sdet_{fid}", use_container_width=True):
                    st.session_state.search_detail = fid
                    st.rerun()
            with col_vu_btn:
                if deja_vu:
                    if st.button("↩️ Retirer des vus", key=f"svu_ret_{fid}", use_container_width=True):
                        vu_retirer(fid)
                        st.rerun()
                else:
                    if st.button("👁 Marquer VU", key=f"svu_{fid}", use_container_width=True):
                        vu_ajouter(fid, titre, annee)
                        avoir_retirer(fid)
                        st.rerun()
            with col_av_btn:
                if deja_avoir:
                    if st.button("↩️ Retirer de À voir", key=f"sav_ret_{fid}", use_container_width=True):
                        avoir_retirer(fid)
                        st.rerun()
                elif not deja_vu:
                    if st.button("🔖 À VOIR", key=f"sav_{fid}", use_container_width=True):
                        avoir_ajouter(fid, titre, annee)
                        st.rerun()

    elif chercher and not st.session_state.search_results:
        st.markdown("""
        <div style="background:#12111e;border:1px solid #22203a;border-radius:12px;
             padding:2rem;text-align:center;max-width:480px;margin:2rem auto;">
            <p style="font-family:'Playfair Display',serif;color:#e8e0d0;">Aucun film trouvé</p>
            <p style="color:#4a4438;font-size:.9rem;">Essayez un autre titre ou vérifiez l'orthographe.</p>
        </div>""", unsafe_allow_html=True)

    elif not st.session_state.search_results:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#12111e,#1a1826);border:1px solid #22203a;
             border-radius:16px;padding:3rem;text-align:center;max-width:500px;margin:3rem auto;">
            <div style="font-size:3rem;margin-bottom:1rem;">🔎</div>
            <p style="font-family:'Playfair Display',serif;font-size:1.2rem;color:#e8e0d0;margin-bottom:.8rem;">
                Chercher un titre précis</p>
            <p style="color:#5a5048;font-size:.9rem;line-height:1.7;">
                Recherchez n'importe quel film dans la base TMDB.<br>
                Ajoutez-le à votre liste <strong style="color:#d4af37;">À Voir</strong> ou marquez-le comme <strong style="color:#d4af37;">Vu</strong>.</p>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 3 — HUMEUR DU SOIR
# ══════════════════════════════════════════════
with tab_humeur:
    st.markdown('<p style="font-family:\'Playfair Display\',serif;font-size:1.5rem;color:#e8e0d0;margin-bottom:.4rem;">Quelle est votre humeur ce soir ?</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#4a4438;font-size:.9rem;margin-bottom:1.5rem;">Décrivez ce que vous ressentez — Gemini choisit pour vous parmi votre sélection actuelle.</p>', unsafe_allow_html=True)

    humeur_input = st.text_area(
        "Votre humeur", height=100,
        placeholder="Ex : j'ai envie d'un film qui me transporte loin, quelque chose de visuellement somptueux et contemplatif…",
        label_visibility="collapsed"
    )

    suggestions = st.selectbox("Ou choisissez une humeur type :", HUMEURS, label_visibility="visible")
    if suggestions != HUMEURS[0] and not humeur_input:
        humeur_input = suggestions

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        demander = st.button("✨ Recommander")

    if demander:
        films_dispo = st.session_state.films_ok
        if not films_dispo:
            st.warning("⚠️ Lancez d'abord une recherche dans l'onglet **Recherche** pour alimenter la sélection.")
        elif not humeur_input or humeur_input == HUMEURS[0]:
            st.warning("Décrivez votre humeur ou choisissez une suggestion.")
        else:
            with st.spinner("Gemini sélectionne vos films…"):
                reponse = recommander_par_humeur(humeur_input, films_dispo)
            st.markdown(f'<div class="ai-response">{reponse.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 4 — À VOIR
# ══════════════════════════════════════════════
with tab_avoir:
    st.markdown('<p style="font-family:\'Playfair Display\',serif;font-size:1.5rem;color:#e8e0d0;margin-bottom:1rem;">🔖 Ma liste À Voir</p>', unsafe_allow_html=True)

    avoir_data = avoir_charger()

    if not avoir_data:
        st.markdown("""
        <div style="background:#12111e;border:1px solid #22203a;border-radius:12px;
             padding:2.5rem;text-align:center;max-width:500px;margin:2rem auto;">
            <div style="font-size:3rem;margin-bottom:.8rem;">🔖</div>
            <p style="font-family:'Playfair Display',serif;color:#e8e0d0;font-size:1.1rem;margin-bottom:.5rem;">Votre liste est vide</p>
            <p style="color:#4a4438;font-size:.9rem;line-height:1.7;">
                Ouvrez le détail d'un film ou utilisez la recherche par titre<br>
                et cliquez sur <strong style="color:#d4af37;">🔖 À VOIR</strong> pour l'ajouter ici.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.metric("Films dans votre liste", len(avoir_data))
        st.divider()

        # Grille 4 colonnes avec jaquettes si possible
        ids_list = list(avoir_data.items())

        # On affiche en grille 4 colonnes avec les détails TMDB
        for i in range(0, len(ids_list), 4):
            cols = st.columns(4, gap="medium")
            for j, (fid, info) in enumerate(ids_list[i:i+4]):
                with cols[j]:
                    # Tenter de récupérer la jaquette depuis TMDB (cached)
                    titre = info.get("titre", "?")
                    annee = info.get("annee", "?")
                    date_ajout = info.get("date", "—")

                    # Récupération légère — uniquement poster + note
                    @st.cache_data(ttl=86400, show_spinner=False)
                    def get_poster_info(mid):
                        try:
                            url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={TMDB_API_KEY}&language=fr-FR"
                            r = requests.get(url, timeout=4)
                            d = r.json()
                            return d.get("poster_path"), d.get("vote_average", 0)
                        except Exception:
                            return None, 0

                    poster_path, note = get_poster_info(int(fid))

                    img_html = (
                        f'<img class="film-poster" src="https://image.tmdb.org/t/p/w400{poster_path}" alt="{titre}" loading="lazy">'
                        if poster_path else '<div class="film-poster-ph">🎬</div>'
                    )

                    st.markdown(f"""
                    <div class="film-card">
                        {img_html}
                        <div class="film-info">
                            <p class="film-title">{titre}</p>
                            <div class="film-meta">
                                <span class="note-badge">★ {note:.1f}</span>
                                <span class="annee-badge">{annee}</span>
                            </div>
                            <p style="font-size:.7rem;color:#3a3428;margin-top:6px;">Ajouté le {date_ajout}</p>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    # Boutons sous la carte
                    col_det2, col_vu2 = st.columns(2)
                    with col_det2:
                        if st.button("ℹ️", key=f"av_det_{fid}", use_container_width=True, help="Détails"):
                            st.session_state.film_detail = int(fid)
                            # Redirige vers l'onglet recherche pour voir le détail
                            st.rerun()
                    with col_vu2:
                        if st.button("👁 VU", key=f"av_vu_{fid}", use_container_width=True):
                            vu_ajouter(int(fid), titre, annee)
                            avoir_retirer(int(fid))
                            st.rerun()

                    if st.button("🗑 Retirer", key=f"av_del_{fid}", use_container_width=True):
                        avoir_retirer(int(fid))
                        st.rerun()

# ══════════════════════════════════════════════
#  TAB 5 — FILMS VUS
# ══════════════════════════════════════════════
with tab_journal:
    st.markdown('<p style="font-family:\'Playfair Display\',serif;font-size:1.5rem;color:#e8e0d0;margin-bottom:1rem;">👁 Films vus</p>', unsafe_allow_html=True)

    vus_data = vu_charger()

    if not vus_data:
        st.markdown("""
        <div style="background:#12111e;border:1px solid #22203a;border-radius:12px;
             padding:2rem;text-align:center;max-width:480px;margin:2rem auto;">
            <div style="font-size:2.5rem;margin-bottom:.8rem;">👁</div>
            <p style="color:#4a4438;font-size:.9rem;">Aucun film marqué comme vu.<br>
            Ouvrez le détail d'un film et cliquez sur <b>Marquer comme VU</b>.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.metric("Films vus", len(vus_data))
        st.divider()
        for fid, info in sorted(vus_data.items(), key=lambda x: x[1].get("date",""), reverse=True):
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f'<div class="journal-entry">'
                    f'<p class="journal-film">{info.get("titre","?")} <span class="annee-badge">({info.get("annee","?")})</span></p>'
                    f'<p class="journal-date">Vu le {info.get("date","—")}</p>'
                    f'</div>', unsafe_allow_html=True)
            with col_del:
                if st.button("🗑", key=f"del_{fid}", help="Retirer"):
                    vu_retirer(fid)
                    st.rerun()
