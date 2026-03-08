import streamlit as st
import requests
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
TMDB_API_KEY  = st.secrets.get("TMDB_API_KEY", "")
GROQ_API_KEY  = st.secrets.get("GROQ_API_KEY", "")
GITHUB_TOKEN  = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO   = "deeperinthenet-droid/cinematheque-marc"
GITHUB_BRANCH = "main"
GH_API        = "https://api.github.com"

st.set_page_config(
    page_title="Cinémathèque · Mr Marc",
    layout="wide",
    page_icon="🎬",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  CSS NETFLIX
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Netflix+Sans:wght@400;500;700&family=Bebas+Neue&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;1,300&display=swap');

/* ── Reset global ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
section.main { 
    background-color: #141414 !important; 
    color: #e5e5e5 !important;
    font-family: 'DM Sans', 'Helvetica Neue', Arial, sans-serif !important;
}

/* ── Cacher éléments Streamlit ── */
#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stSidebarHeader"], [data-testid="stSidebarCollapseButton"],
[data-testid="stToolbar"], header { display: none !important; }

[data-testid="stSidebar"] { display: none !important; }

/* Supprimer padding/margin streamlit */
[data-testid="stMainBlockContainer"] { 
    padding: 0 !important; 
    max-width: 100% !important;
}
[data-testid="block-container"] {
    padding: 0 !important;
    max-width: 100% !important;
}
.main .block-container { padding: 0 !important; max-width: 100% !important; }

/* ── NAVBAR ── */
.nf-navbar {
    position: sticky; top: 0; z-index: 1000;
    background: linear-gradient(180deg, rgba(20,20,20,1) 0%, rgba(20,20,20,0.85) 80%, transparent 100%);
    padding: 0 4% ;
    display: flex; align-items: center; gap: 32px;
    backdrop-filter: blur(4px);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    height: 68px;
}
.nf-logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem; color: #e50914; letter-spacing: 2px;
    text-decoration: none; white-space: nowrap;
    text-shadow: 0 0 30px rgba(229,9,20,0.4);
}
.nf-nav-links { display: flex; gap: 20px; align-items: center; flex: 1; }
.nf-nav-link {
    font-size: .85rem; color: #e5e5e5; text-decoration: none;
    opacity: 0.75; transition: opacity .2s; white-space: nowrap;
    cursor: pointer; padding: 4px 0;
}
.nf-nav-link:hover { opacity: 1; }
.nf-nav-link.active { opacity: 1; font-weight: 600; }

/* ── HERO BANNER ── */
.nf-hero {
    position: relative; width: 100%;
    height: 520px; overflow: hidden;
    background: #000;
}
.nf-hero-bg {
    position: absolute; inset: 0;
    background-size: cover; background-position: center 20%;
    filter: brightness(0.45);
    transition: background-image 1s ease;
}
.nf-hero-gradient {
    position: absolute; inset: 0;
    background: linear-gradient(
        to right, rgba(20,20,20,0.95) 0%, rgba(20,20,20,0.6) 40%, transparent 70%
    ),
    linear-gradient(
        to top, rgba(20,20,20,1) 0%, transparent 40%
    );
}
.nf-hero-content {
    position: relative; z-index: 10;
    padding: 100px 4% 0;
    max-width: 580px;
}
.nf-hero-maturity {
    display: inline-block;
    border: 1px solid rgba(255,255,255,0.4);
    color: #fff; font-size: .7rem; padding: 2px 8px;
    margin-bottom: 12px; letter-spacing: 1px;
    text-transform: uppercase;
}
.nf-hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem; color: #fff; line-height: 1;
    margin-bottom: 16px; letter-spacing: 1px;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
}
.nf-hero-meta {
    display: flex; gap: 12px; align-items: center;
    margin-bottom: 16px; flex-wrap: wrap;
}
.nf-hero-score { color: #46d369; font-weight: 700; font-size: .9rem; }
.nf-hero-year  { color: #bcbcbc; font-size: .85rem; }
.nf-hero-dur   { color: #bcbcbc; font-size: .85rem; }
.nf-hero-desc {
    font-size: .9rem; color: #e5e5e5; line-height: 1.6;
    margin-bottom: 24px; opacity: 0.9;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.nf-hero-btns { display: flex; gap: 12px; flex-wrap: wrap; }
.nf-btn-play {
    background: #fff; color: #000;
    border: none; border-radius: 4px;
    padding: 10px 28px; font-weight: 700; font-size: .95rem;
    cursor: pointer; display: flex; align-items: center; gap: 8px;
    transition: background .15s;
}
.nf-btn-play:hover { background: rgba(255,255,255,0.8); }
.nf-btn-more {
    background: rgba(109,109,110,0.7); color: #fff;
    border: none; border-radius: 4px;
    padding: 10px 24px; font-weight: 600; font-size: .95rem;
    cursor: pointer; display: flex; align-items: center; gap: 8px;
    transition: background .15s; backdrop-filter: blur(4px);
}
.nf-btn-more:hover { background: rgba(109,109,110,0.5); }

/* ── SECTIONS / ROWS ── */
.nf-section { padding: 0 4% 32px; margin-top: -60px; position: relative; z-index: 10; }
.nf-section-title {
    font-size: 1.25rem; font-weight: 700; color: #e5e5e5;
    margin-bottom: 12px; letter-spacing: .3px;
}
.nf-section-title span {
    color: #46d369; font-size: .85rem; font-weight: 500;
    margin-left: 12px; letter-spacing: 1px; text-transform: uppercase;
}

/* ── ROW SCROLL ── */
.nf-row {
    display: flex; gap: 6px; overflow-x: auto;
    padding-bottom: 8px; scroll-behavior: smooth;
    scrollbar-width: thin; scrollbar-color: #555 transparent;
}
.nf-row::-webkit-scrollbar { height: 4px; }
.nf-row::-webkit-scrollbar-track { background: transparent; }
.nf-row::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }

/* ── CARD — image HTML + bouton transparent par-dessus ── */

.nf-card-container {
    position: relative;
    border-radius: 4px;
    overflow: visible;
    margin-bottom: 0;
}

/* L'image jaquette — SANS animation hover */
.nf-card-img-wrap {
    position: relative;
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    z-index: 1;
}

.nf-card-img-wrap img {
    width: 100%; aspect-ratio: 2/3;
    object-fit: cover; display: block;
}

.nf-card-img-ph {
    width: 100%; aspect-ratio: 2/3;
    background: linear-gradient(135deg,#1f1f1f,#2a2a2a);
    display: flex; align-items: center; justify-content: center;
    font-size: 2.5rem; color: #444;
}

/* Icône ▶ et overlay désactivés */
.nf-card-play { display: none; }
.nf-card-overlay { display: none; }

/* Badges VU / À VOIR */
.nf-card-badges {
    position: absolute; top: 5px; right: 5px;
    display: flex; flex-direction: column; gap: 3px;
    z-index: 6; pointer-events: none;
}
.nf-badge-vu    { background:#46d369; color:#000; font-size:.52rem; font-weight:700; padding:2px 5px; border-radius:2px; display:inline-block; }
.nf-badge-avoir { background:#e50914; color:#fff; font-size:.52rem; font-weight:700; padding:2px 5px; border-radius:2px; display:inline-block; }

.nf-card-title { font-size:.73rem; font-weight:700; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:3px; }
.nf-card-meta  { display:flex; gap:5px; align-items:center; flex-wrap:wrap; }
.nf-card-score { color:#46d369; font-size:.65rem; font-weight:700; }
.nf-card-year  { color:#bcbcbc; font-size:.63rem; }
.nf-card-plat  { background:rgba(229,9,20,.2); border:1px solid rgba(229,9,20,.4); color:#ff6b6b; font-size:.52rem; padding:1px 4px; border-radius:2px; }

/* Bouton Détails sous la jaquette — rouge Netflix */
.nf-card-btn > div[data-testid="stButton"] > button,
.nf-card-btn > div.stButton > button {
    background: #e50914 !important;
    border: none !important;
    border-radius: 0 0 4px 4px !important;
    color: #fff !important;
    font-size: .72rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    padding: 5px 0 !important;
    min-height: 26px !important;
    width: 100% !important;
    cursor: pointer !important;
    margin-top: 0 !important;
}
.nf-card-btn > div[data-testid="stButton"] > button:hover,
.nf-card-btn > div.stButton > button:hover {
    background: #f40612 !important;
}

/* Bouton RETOUR — rouge, en haut */
.nf-retour-btn > div[data-testid="stButton"] > button,
.nf-retour-btn > div.stButton > button {
    background: #e50914 !important;
    border: none !important;
    border-radius: 4px !important;
    color: #fff !important;
    font-size: .85rem !important;
    font-weight: 700 !important;
    padding: 8px 20px !important;
    margin-bottom: 20px !important;
}
.nf-retour-btn > div[data-testid="stButton"] > button:hover,
.nf-retour-btn > div.stButton > button:hover {
    background: #f40612 !important;
}

/* ── MODAL DÉTAIL ── */
.nf-modal-wrap {
    background: #181818; border-radius: 8px;
    overflow: hidden; margin: 24px 0; 
    box-shadow: 0 16px 64px rgba(0,0,0,0.9);
    border: 1px solid rgba(255,255,255,0.08);
}
.nf-modal-banner {
    position: relative; height: 320px; overflow: hidden;
}
.nf-modal-banner img {
    width: 100%; height: 100%; object-fit: cover; object-position: center 20%;
    filter: brightness(0.55);
}
.nf-modal-banner-gradient {
    position: absolute; inset: 0;
    background: linear-gradient(to top, #181818 0%, transparent 50%),
                linear-gradient(to right, rgba(24,24,24,0.8) 0%, transparent 60%);
}
.nf-modal-banner-content {
    position: absolute; bottom: 24px; left: 28px; right: 28px;
}
.nf-modal-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.4rem; color: #fff; margin-bottom: 12px; letter-spacing: 1px;
}
.nf-modal-body { padding: 0 28px 28px; }
.nf-modal-meta {
    display: flex; gap: 14px; align-items: center;
    margin-bottom: 16px; flex-wrap: wrap;
}
.nf-modal-score { color: #46d369; font-weight: 700; }
.nf-modal-year, .nf-modal-dur { color: #bcbcbc; font-size: .85rem; }
.nf-modal-overview { color: #d2d2d2; line-height: 1.7; font-size: .9rem; margin-bottom: 20px; }
.nf-lbl {
    font-size: .7rem; text-transform: uppercase; letter-spacing: 2px;
    color: #777; margin: 14px 0 6px;
}
.nf-chip {
    display: inline-block; background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12); color: #ccc;
    font-size: .75rem; padding: 4px 10px; border-radius: 3px; margin: 2px;
}
.nf-plat-chip {
    display: inline-block; background: rgba(229,9,20,0.1);
    border: 1px solid rgba(229,9,20,0.3); color: #ff6b6b;
    font-size: .75rem; padding: 4px 10px; border-radius: 3px; margin: 2px;
}

/* ── SEARCH ── */
.nf-search-bar {
    background: #141414; padding: 20px 4%;
    display: flex; gap: 12px; align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* ── À VOIR / VUS LIST ── */
.nf-list-item {
    display: flex; gap: 16px; align-items: center;
    background: #1f1f1f; border-radius: 4px;
    padding: 12px 16px; margin-bottom: 8px;
    border: 1px solid rgba(255,255,255,0.06);
    transition: background .2s;
}
.nf-list-item:hover { background: #2a2a2a; }
.nf-list-thumb {
    width: 50px; min-width: 50px; height: 72px;
    border-radius: 3px; object-fit: cover;
}
.nf-list-ph {
    width: 50px; min-width: 50px; height: 72px;
    background: #2a2a2a; border-radius: 3px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
}
.nf-list-title { font-size: .95rem; font-weight: 600; color: #e5e5e5; margin-bottom: 4px; }
.nf-list-sub   { font-size: .78rem; color: #777; }

/* ── AI HUMEUR ── */
.nf-ai-box {
    background: #1f1f1f;
    border-left: 3px solid #e50914;
    border-radius: 0 6px 6px 0;
    padding: 20px 24px; margin-top: 16px;
    font-size: .9rem; color: #d2d2d2; line-height: 1.8;
}

/* ── FILTRES SIDEBAR-LIKE ── */
.nf-filters {
    background: #1a1a1a; padding: 16px 4%;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap;
}
.nf-filter-lbl { font-size: .68rem; text-transform: uppercase; letter-spacing: 1.5px; color: #666; margin-bottom: 4px; }

/* Boutons plateformes — petits chips */
[data-testid="column"] div.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #888 !important;
    font-size: .62rem !important;
    font-weight: 500 !important;
    padding: 3px 6px !important;
    min-height: 24px !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    border-radius: 3px !important;
}
[data-testid="column"] div.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.12) !important;
    color: #ccc !important;
}
[data-testid="column"] div.stButton > button[kind="primary"] {
    background: rgba(229,9,20,0.25) !important;
    border: 1px solid rgba(229,9,20,0.6) !important;
    color: #ff6b6b !important;
    font-size: .62rem !important;
    font-weight: 700 !important;
    padding: 3px 6px !important;
    min-height: 24px !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    border-radius: 3px !important;
}

/* Streamlit inputs style override */
[data-testid="stTextInput"] input {
    background: #2a2a2a !important; border: 1px solid #444 !important;
    color: #e5e5e5 !important; border-radius: 4px !important;
    font-size: .9rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #e50914 !important;
    box-shadow: 0 0 0 2px rgba(229,9,20,0.2) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #2a2a2a !important; border: 1px solid #444 !important;
    border-radius: 4px !important; color: #e5e5e5 !important;
}
.stSlider [data-testid="stSliderThumb"]     { background: #e50914 !important; }
.stSlider [data-testid="stSliderTrackFill"] { background: #e50914 !important; }
[data-testid="stMultiSelect"] > div {
    background: #2a2a2a !important; border: 1px solid #444 !important;
}

/* Boutons streamlit */
div.stButton > button {
    background: #e50914 !important; color: #fff !important;
    border: none !important; border-radius: 4px !important;
    font-weight: 600 !important; font-size: .82rem !important;
    padding: 6px 14px !important; transition: background .15s !important;
}
div.stButton > button:hover { background: #f40612 !important; }

/* Bouton secondaire */
div.stButton > button[kind="secondary"] {
    background: rgba(109,109,110,0.6) !important;
    color: #fff !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: rgba(109,109,110,0.4) !important;
}

/* Tabs */
[data-testid="stTabs"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
}
[data-testid="stTabs"] button {
    font-size: .82rem !important; color: #aaa !important;
    text-transform: uppercase !important; letter-spacing: 1px !important;
    font-weight: 500 !important;
    background: transparent !important;
    border: none !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #fff !important;
    border-bottom: 2px solid #e50914 !important;
}
[data-testid="stTabPanel"] { padding: 0 !important; }

/* Toggle */
[data-testid="stToggle"] label span { color: #e5e5e5 !important; }

/* Metric */
[data-testid="stMetric"] { background: #1f1f1f !important; border-radius: 6px; padding: 12px !important; }
[data-testid="stMetricValue"] { color: #e50914 !important; font-family: 'Bebas Neue', sans-serif !important; font-size: 2rem !important; }
[data-testid="stMetricLabel"] { color: #777 !important; font-size: .75rem !important; text-transform: uppercase !important; }

/* Spinner */
[data-testid="stSpinner"] { color: #e50914 !important; }

/* Alerte / warning */
[data-testid="stAlert"] { background: #1f1f1f !important; border-left-color: #e50914 !important; color: #e5e5e5 !important; }

/* Video */
[data-testid="stVideo"] { border-radius: 6px; overflow: hidden; }

/* Columns gap reset */
[data-testid="column"] { padding: 0 4px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DONNÉES
# ─────────────────────────────────────────────
MES_PLATEFORMES = {
    # Généralistes
    "Netflix": 8, "Disney+": 337, "Amazon": 119, "Max": 1899,
    "Apple TV+": 350,
    "Arte": 234, "France TV": 312, "MyTF1 Max": 1870,
    "6play Max": 1866, "OCS": 56,
    # Famille Canal+
    "Canal+": 381,
    "Canal+ Docs": 1754,
    "Paramount+": 531,
    "myCANAL": 635,
}
GENRES = {
    "Action": 28, "Animation": 16, "Aventure": 12, "Comédie": 35,
    "Crime": 80, "Documentaire": 99, "Drame": 18, "Familial": 10751,
    "Fantastique": 14, "Guerre": 10752, "Histoire": 36, "Horreur": 27,
    "Musique": 10402, "Mystère": 9648, "Romance": 10749,
    "Science-Fiction": 878, "Thriller": 53, "Western": 37,
}
COLLECTIONS = {
    "🌟 Standard": "none", "🏆 Primés": "awards",
    "🇫🇷 Français": "french", "🎞️ Noir & Blanc": "bw",
    "🕰️ Classiques": "classics", "💎 Pépites": "hidden_gems",
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
#  PERSISTANCE GITHUB + CACHE SESSION
# ─────────────────────────────────────────────
import base64
from threading import Thread

def _gh_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def _gh_read(filename):
    """Lit un fichier JSON depuis GitHub, retourne (data_dict, sha)."""
    try:
        url = f"{GH_API}/repos/{GITHUB_REPO}/contents/{filename}?ref={GITHUB_BRANCH}"
        r = requests.get(url, headers=_gh_headers(), timeout=10)
        if r.status_code == 404:
            return {}, None
        r.raise_for_status()
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return json.loads(content), r.json()["sha"]
    except:
        return {}, None

def _gh_write(filename, data, sha=None):
    """Écrit un fichier JSON sur GitHub (appelé en arrière-plan)."""
    try:
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
        url = f"{GH_API}/repos/{GITHUB_REPO}/contents/{filename}"
        payload = {"message": f"update {filename}", "content": content, "branch": GITHUB_BRANCH}
        if sha: payload["sha"] = sha
        requests.put(url, headers=_gh_headers(), json=payload, timeout=15)
    except:
        pass

def _gh_write_async(filename, data, sha=None):
    """Écrit sur GitHub en arrière-plan sans bloquer l'UI."""
    Thread(target=_gh_write, args=(filename, data, sha), daemon=True).start()

def _init_cache():
    """Charge VU et AVOIR depuis GitHub une seule fois par session."""
    if "vu_data" not in st.session_state or "avoir_data" not in st.session_state:
        vu, vu_sha     = _gh_read("films_vus.json")
        av, av_sha     = _gh_read("films_avoir.json")
        st.session_state.vu_data    = vu
        st.session_state.vu_sha     = vu_sha
        st.session_state.avoir_data = av
        st.session_state.avoir_sha  = av_sha

# ── VU ──
def vu_charger():
    _init_cache()
    return st.session_state.vu_data

def vu_ajouter(fid, titre, annee):
    _init_cache()
    st.session_state.vu_data[str(fid)] = {"titre": titre, "annee": annee, "date": datetime.now().strftime("%d/%m/%Y")}
    _gh_write_async("films_vus.json", st.session_state.vu_data, st.session_state.vu_sha)

def vu_retirer(fid):
    _init_cache()
    st.session_state.vu_data.pop(str(fid), None)
    _gh_write_async("films_vus.json", st.session_state.vu_data, st.session_state.vu_sha)

def vu_ids():
    _init_cache()
    return set(st.session_state.vu_data.keys())

# ── À VOIR ──
def avoir_charger():
    _init_cache()
    return st.session_state.avoir_data

def avoir_ajouter(fid, titre, annee):
    _init_cache()
    st.session_state.avoir_data[str(fid)] = {"titre": titre, "annee": annee, "date": datetime.now().strftime("%d/%m/%Y")}
    _gh_write_async("films_avoir.json", st.session_state.avoir_data, st.session_state.avoir_sha)

def avoir_retirer(fid):
    _init_cache()
    st.session_state.avoir_data.pop(str(fid), None)
    _gh_write_async("films_avoir.json", st.session_state.avoir_data, st.session_state.avoir_sha)

def avoir_ids():
    _init_cache()
    return set(st.session_state.avoir_data.keys())

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
    if col_key == "awards":     params["vote_count.gte"] = 1000
    elif col_key == "french":   params["with_original_language"] = "fr"
    elif col_key == "bw":       params["with_keywords"] = "2343"
    elif col_key == "classics": params["primary_release_date.lte"] = "1975-01-01"
    elif col_key == "hidden_gems": params["vote_count.gte"] = 50; params["vote_count.lte"] = 500
    if genre_ids: params["with_genres"] = genre_ids
    if annee_min and col_key != "classics":
        params["primary_release_date.gte"] = f"{annee_min}-01-01"
    try:
        r = requests.get("https://api.themoviedb.org/3/discover/movie", params=params, timeout=6)
        r.raise_for_status()
        return r.json().get("results", [])
    except: return []

@st.cache_data(ttl=600, show_spinner=False)
def rechercher_par_nom(query: str):
    if not query or len(query.strip()) < 2: return []
    try:
        r = requests.get("https://api.themoviedb.org/3/search/movie", params={
            "api_key": TMDB_API_KEY, "language": "fr-FR",
            "query": query.strip(), "include_adult": False, "page": 1,
        }, timeout=6)
        return r.json().get("results", [])[:12]
    except: return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_plateformes_tmdb(movie_id):
    try:
        data = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}",
            timeout=4).json()
        flat = data.get("results", {}).get("FR", {}).get("flatrate", [])
        return [p["provider_name"] for p in flat if p["provider_name"] in MES_PLATEFORMES]
    except: return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_plateformes(movie_id, titre="", annee=""):
    return get_plateformes_tmdb(movie_id)

@st.cache_data(ttl=3600, show_spinner=False)
def get_details(movie_id):
    try:
        r = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=fr-FR&append_to_response=credits,videos,keywords",
            timeout=5)
        return r.json()
    except: return {}

@st.cache_data(ttl=86400, show_spinner=False)
def get_poster_note(mid):
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{mid}?api_key={TMDB_API_KEY}&language=fr-FR", timeout=4)
        d = r.json()
        return d.get("poster_path"), d.get("backdrop_path"), d.get("vote_average", 0), d.get("overview", ""), d.get("runtime", 0)
    except: return None, None, 0, "", 0

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
            r = fut.result()
            if r: films_ok.append(r)
            if len(films_ok) >= max_films: break
    return films_ok

# ─────────────────────────────────────────────
#  GEMINI
# ─────────────────────────────────────────────
def recommander_par_humeur(humeur: str, films: list) -> str:
    if not GROQ_API_KEY:
        return "⚠️ Clé API Groq non configurée — créez un compte gratuit sur groq.com et ajoutez `GROQ_API_KEY` dans vos secrets Streamlit."

    catalogue = "\n".join(
        f"- {f['title']} ({f.get('release_date','')[:4]}) — {f.get('vote_average',0):.1f}/10 | {', '.join(f.get('offres',[]))}"
        for f in films[:20])
    prompt = f"""Tu es le programmateur d'une cinémathèque de prestige parisienne.
Mr Marc exprime cette envie ce soir : « {humeur} »
Films disponibles :
{catalogue}
Sélectionne 3 films parfaits pour son envie. Pour chacun : titre exact, phrase d'accroche cinéphile, raison précise.
Pas d'introduction. Ton des Cahiers du Cinéma."""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=20
        )
        data = r.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        if "error" in data:
            return f"⚠️ Erreur Groq : {data['error'].get('message', data['error'])}"

        return f"⚠️ Réponse inattendue : {data}"

    except requests.exceptions.Timeout:
        return "⚠️ Groq ne répond pas (timeout). Réessayez."
    except Exception as e:
        return f"⚠️ Erreur inattendue : {e}"

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for k, v in [
    ("films_ok", []), ("film_detail", None),
    ("search_results", []), ("search_query", None), ("search_detail", None),
    ("hero_idx", 0),
]:
    if k not in st.session_state: st.session_state[k] = v

# ─────────────────────────────────────────────
#  CACHE LOCAL
# ─────────────────────────────────────────────
CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache_films.json")

@st.cache_data(ttl=3600)
def charger_cache_local():
    """Charge le cache JSON pré-calculé s'il existe."""
    if not os.path.exists(CACHE_FILE):
        return [], None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        films   = data.get("films", [])
        updated = data.get("updated_at", "")[:10]
        return films, updated
    except Exception:
        return [], None

GENRES_EXCLUS_MARCEL = {27, 10749, 53}  # Horreur, Romance/Érotique, Thriller violent

def filtrer_cache(films, genre_ids=None, provider_ids=None, annee_min=1930, annee_max=2026, note_mini=7.5, tri="vote_average.desc", ok_marcel=False):
    """Filtre et trie les films du cache selon les critères."""
    genre_id_list = [int(g) for g in genre_ids.split(",")] if genre_ids else []
    prov_id_list  = [int(p) for p in provider_ids.split("|")] if provider_ids else []
    result = []

    for f in films:
        if f.get("vote_average", 0) < note_mini:
            continue
        annee = int((f.get("release_date") or "1900")[:4])
        if annee < annee_min or annee > annee_max:
            continue
        if f.get("adult", False):
            if ok_marcel:
                continue
        film_genres = [g["id"] if isinstance(g, dict) else g for g in f.get("genres", [])]
        if ok_marcel and any(g in GENRES_EXCLUS_MARCEL for g in film_genres):
            continue
        if genre_id_list:
            if not any(g in film_genres for g in genre_id_list):
                continue
        if prov_id_list:
            film_prov_ids = [MES_PLATEFORMES[o] for o in f.get("offres", []) if o in MES_PLATEFORMES]
            if not any(p in film_prov_ids for p in prov_id_list):
                continue
        result.append(f)

    if tri == "vote_average.desc":
        result.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
    elif tri == "popularity.desc":
        result.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    elif tri == "primary_release_date.desc":
        result.sort(key=lambda x: x.get("release_date", ""), reverse=True)
    elif tri == "primary_release_date.asc":
        result.sort(key=lambda x: x.get("release_date", ""))
    return result

# ─────────────────────────────────────────────
#  COMPOSANTS
# ─────────────────────────────────────────────
def render_card(film, prefix="c"):
    fid    = film["id"]
    titre  = film.get("title", "?")
    note   = film.get("vote_average", 0)
    annee  = film.get("release_date", "")[:4] or "—"
    offres = film.get("offres", [])
    poster = film.get("poster_path")
    deja_vu    = str(fid) in vu_ids()
    deja_avoir = str(fid) in avoir_ids()

    img_src  = f"https://image.tmdb.org/t/p/w300{poster}" if poster else ""
    plats    = "".join(f'<span class="nf-card-plat">{o}</span>' for o in offres[:2])
    badge_vu    = '<span class="nf-badge-vu">VU</span>'        if deja_vu    else ""
    badge_avoir = '<span class="nf-badge-avoir">À VOIR</span>' if deja_avoir else ""

    # Image HTML visible avec hover CSS
    img_content = (
        f'<img src="{img_src}" alt="{titre}" loading="lazy">'
        if img_src else '<div class="nf-card-img-ph">🎬</div>'
    )

    st.markdown(f"""
    <div class="nf-card-container">
        <div class="nf-card-img-wrap">
            {img_content}
            <div class="nf-card-play">&#9654;</div>
            <div class="nf-card-badges">{badge_vu}{badge_avoir}</div>
            <div class="nf-card-overlay">
                <div class="nf-card-title">{titre}</div>
                <div class="nf-card-meta">
                    <span class="nf-card-score">&#9654; {note:.1f}</span>
                    <span class="nf-card-year">{annee}</span>
                    {plats}
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Boutons Détails + VU sous la jaquette
    col_det, col_vu = st.columns([3, 2])
    with col_det:
        if st.button("▶ Détails", key=f"{prefix}_det_{fid}", use_container_width=True):
            st.session_state.film_detail = fid
            st.rerun()
    with col_vu:
        if deja_vu:
            if st.button("✅ VU", key=f"{prefix}_vu_{fid}", use_container_width=True):
                vu_retirer(fid)
                st.rerun()
        else:
            if st.button("👁 VU", key=f"{prefix}_vu_{fid}", use_container_width=True):
                vu_ajouter(fid, titre, annee)
                avoir_retirer(fid)
                st.rerun()

def render_detail(film_id):
    # Scroll en haut de page
    st.markdown('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)
    st.components.v1.html("<script>window.parent.scrollTo(0, 0);</script>", height=0)

    d = get_details(film_id)
    if not d: st.warning("Impossible de charger les détails."); return

    titre  = d.get("title", "")
    annee  = d.get("release_date", "")[:4] or "—"
    note   = d.get("vote_average", 0)
    votes  = d.get("vote_count", 0)
    duree  = d.get("runtime", 0)
    duree_fmt = f"{duree//60}h{duree%60:02d}" if duree else "—"
    overview = d.get("overview", "")
    backdrop = d.get("backdrop_path", "")
    poster   = d.get("poster_path", "")
    tagline  = d.get("tagline", "")

    genres = [g["name"] for g in d.get("genres", [])]
    # Utilise les champs pré-extraits du cache si disponibles, sinon extrait depuis TMDB
    reals  = d.get("directors") or [c["name"] for c in d.get("credits", {}).get("crew", []) if c.get("job") == "Director"]
    cast   = d.get("cast") or [c["name"] for c in d.get("credits", {}).get("cast", [])[:8]]
    trailer_key = d.get("trailer_key")
    if not trailer_key:
        videos = d.get("videos", {}).get("results", [])
        t = next((v for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)
        trailer_key = t["key"] if t else None

    # Scroll en haut de page à l'ouverture du détail
    st.markdown('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)
    st.components.v1.html("<script>window.parent.scrollTo(0, 0);</script>", height=0)

    # Plateformes — priorité au cache local, sinon appel TMDB
    cache_films, _ = charger_cache_local()
    offres = []
    if cache_films:
        film_cache = next((f for f in cache_films if f["id"] == film_id), None)
        if film_cache:
            offres = film_cache.get("offres", [])
    if not offres:
        offres = get_plateformes_tmdb(film_id)

    vus    = vu_ids()
    avoirs = avoir_ids()
    deja_vu    = str(film_id) in vus
    deja_avoir = str(film_id) in avoirs

    # Banner
    banner_url = f"https://image.tmdb.org/t/p/w1280{backdrop}" if backdrop else ""
    poster_url = f"https://image.tmdb.org/t/p/w400{poster}"   if poster   else ""

    st.markdown(f"""
    <div class="nf-modal-banner">
        {"<img src='" + banner_url + "' alt='" + titre + "'>" if banner_url else ""}
        <div class="nf-modal-banner-gradient"></div>
        <div class="nf-modal-banner-content">
            <div class="nf-modal-title">{titre}</div>
            <div class="nf-modal-meta">
                <span class="nf-modal-score">▶ {note:.1f} ({votes:,} votes)</span>
                <span class="nf-modal-year">{annee}</span>
                <span class="nf-modal-dur">⏱ {duree_fmt}</span>
                {"<span style='color:#bcbcbc;font-size:.8rem;font-style:italic'>« " + tagline + " »</span>" if tagline else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Contenu principal
    col_txt, col_img = st.columns([2, 1], gap="large")

    with col_txt:
        # ← RETOUR en haut, en rouge
        if st.button("← Retour à la sélection", key=f"md_back_{film_id}"):
            st.session_state.film_detail = None
            st.session_state.search_detail = None
            st.rerun()

        if overview:
            st.markdown(f'<p class="nf-modal-overview">{overview}</p>', unsafe_allow_html=True)

        # Plateformes — affiché en priorité juste après le synopsis
        st.markdown('<p class="nf-lbl">Disponible sur</p>', unsafe_allow_html=True)
        if offres:
            st.markdown("".join(f'<span class="nf-plat-chip" style="font-size:.85rem;padding:4px 12px;">▶ {o}</span>' for o in offres), unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#666;font-size:.8rem;">Non disponible sur vos plateformes actuellement</span>', unsafe_allow_html=True)

        if genres:
            st.markdown('<p class="nf-lbl">Genres</p>', unsafe_allow_html=True)
            st.markdown("".join(f'<span class="nf-chip">{g}</span>' for g in genres), unsafe_allow_html=True)

        if reals:
            st.markdown('<p class="nf-lbl">Réalisateur</p>', unsafe_allow_html=True)
            st.markdown("".join(f'<span class="nf-chip">🎬 {r}</span>' for r in reals), unsafe_allow_html=True)

        if cast:
            st.markdown('<p class="nf-lbl">Distribution</p>', unsafe_allow_html=True)
            st.markdown("".join(f'<span class="nf-chip">{a}</span>' for a in cast), unsafe_allow_html=True)

        # Boutons suivi
        st.markdown('<p class="nf-lbl">Mon suivi</p>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if deja_vu:
                if st.button("↩️ Retirer des vus", key=f"md_ret_vu_{film_id}"):
                    vu_retirer(film_id); st.rerun()
            else:
                if st.button("✅ Marquer VU", key=f"md_vu_{film_id}"):
                    vu_ajouter(film_id, titre, annee); avoir_retirer(film_id); st.rerun()
        with col_b:
            if deja_avoir:
                if st.button("↩️ Retirer de À voir", key=f"md_ret_av_{film_id}"):
                    avoir_retirer(film_id); st.rerun()
            elif not deja_vu:
                if st.button("🔖 Ajouter À VOIR", key=f"md_av_{film_id}"):
                    avoir_ajouter(film_id, titre, annee); st.rerun()

    with col_img:
        if poster_url:
            st.image(poster_url, use_container_width=True)
        if trailer_key:
            st.video(f"https://www.youtube.com/watch?v={trailer_key}")

# ─────────────────────────────────────────────
#  NAVBAR HTML
# ─────────────────────────────────────────────
st.markdown("""
<div class="nf-navbar">
    <span class="nf-logo">CINÉMARC</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TABS PRINCIPAUX
# ─────────────────────────────────────────────
tab_browse, tab_search, tab_avoir, tab_vus = st.tabs([
    "🎬  Catalogue",
    "🔍  Recherche",
    "🔖  À Voir",
    "✅  Vus",
])

# ══════════════════════════════════════════════
#  TAB 1 — CATALOGUE STYLE NETFLIX
# ══════════════════════════════════════════════
with tab_browse:

    # ── Filtres horizontaux ──
    # Init plateformes sélectionnées
    with st.container():
        st.markdown('<div style="background:#1a1a1a;padding:12px 4% 8px;border-bottom:1px solid rgba(255,255,255,0.06);">', unsafe_allow_html=True)
        f1, f2, f3, f4, f6 = st.columns([2, 1.5, 1.5, 2, 0.8])
        with f1:
            st.markdown('<p class="nf-filter-lbl">Genres</p>', unsafe_allow_html=True)
            genres_sel = st.multiselect("Genres", list(GENRES.keys()), label_visibility="collapsed", placeholder="Tous les genres")
        with f2:
            st.markdown('<p class="nf-filter-lbl">Collection</p>', unsafe_allow_html=True)
            col_sel = st.selectbox("Collection", list(COLLECTIONS.keys()), label_visibility="collapsed")
        with f3:
            st.markdown('<p class="nf-filter-lbl">Trier par</p>', unsafe_allow_html=True)
            tri_sel = st.selectbox("Tri", list(TRIS.keys()), index=1, label_visibility="collapsed")
        with f4:
            st.markdown('<p class="nf-filter-lbl">Période</p>', unsafe_allow_html=True)
            annee_range = st.slider("Période", 1930, 2026, (2000, 2026), label_visibility="collapsed")
            annee_min, annee_max = annee_range
        with f6:
            st.markdown('<p class="nf-filter-lbl">&nbsp;</p>', unsafe_allow_html=True)
            lancer = st.button("▶ Lancer", use_container_width=True)

    # ── OK Marcel ──
    st.markdown('<div style="background:#111;padding:6px 4%;border-bottom:1px solid rgba(255,255,255,0.04);">', unsafe_allow_html=True)
    ok_marcel = st.checkbox("👦 OK Marcel — adapté pour un enfant de 14 ans (exclut Horreur, films érotiques et violence extrême)", value=False)

    # Toutes les plateformes toujours actives
    plats_sel   = list(MES_PLATEFORMES.keys())
    provider_id = None

    genre_ids = ",".join(str(GENRES[g]) for g in genres_sel) if genres_sel else None
    col_key   = COLLECTIONS[col_sel]
    tri_val   = TRIS[tri_sel]

    # ── Affichage statut cache ──
    cache_films, cache_date = charger_cache_local()
    if cache_films:
        st.markdown(
            f'<p style="color:#46d369;font-size:.72rem;margin:4px 0 0 2px;">✅ Cache local disponible — {len(cache_films)} films · mis à jour le {cache_date}</p>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<p style="color:#888;font-size:.72rem;margin:4px 0 0 2px;">⚡ Pas de cache local — chargement depuis TMDB</p>',
            unsafe_allow_html=True)

    if lancer:
        with st.spinner("Chargement du catalogue…"):
            if cache_films:
                # ── PRIORITÉ : cache local (instantané) ──
                resultats = filtrer_cache(
                    cache_films,
                    genre_ids   = genre_ids,
                    provider_ids= provider_id,
                    annee_min   = annee_min,
                    annee_max   = annee_max,
                    note_mini   = 7.5,
                    tri         = tri_val,
                    ok_marcel   = ok_marcel,
                )
                st.session_state.films_ok = resultats
            else:
                # ── FALLBACK : TMDB en direct ──
                brut  = rechercher_films(genre_ids, provider_id, col_key, annee_min, 7.5, tri_val, 1)
                brut += rechercher_films(genre_ids, provider_id, col_key, annee_min, 7.5, tri_val, 2)
                # Filtre annee_max et ok_marcel sur le brut
                if annee_max < 2026:
                    brut = [f for f in brut if int((f.get("release_date") or "9999")[:4]) <= annee_max]
                if ok_marcel:
                    brut = [f for f in brut if not f.get("adult") and not any(
                        g["id"] in GENRES_EXCLUS_MARCEL for g in f.get("genres", []) if isinstance(g, dict))]
                seen, brut_u = set(), []
                for f in brut:
                    if f["id"] not in seen: seen.add(f["id"]); brut_u.append(f)
                st.session_state.films_ok = enrichir_parallel(brut_u, max_films=24)
            st.session_state.film_detail = None

    films = st.session_state.films_ok

    # ── Détail modal ──
    if st.session_state.film_detail:

        render_detail(st.session_state.film_detail)

    elif films:
        # ── HERO BANNER — premier film ──
        hero = films[0]
        hero_backdrop = hero.get("backdrop_path", "")
        hero_title    = hero.get("title", "")
        hero_note     = hero.get("vote_average", 0)
        hero_annee    = hero.get("release_date", "")[:4]
        hero_desc     = hero.get("overview", "")[:220] + "…"
        hero_offres   = hero.get("offres", [])
        hero_img      = f"https://image.tmdb.org/t/p/w1280{hero_backdrop}" if hero_backdrop else ""

        plat_html = "".join(f'<span class="nf-plat-chip" style="font-size:.7rem;padding:2px 7px;">▶ {o}</span>' for o in hero_offres)

        st.markdown(f"""
        <div class="nf-hero">
            {"<div class='nf-hero-bg' style='background-image:url(" + hero_img + ");'></div>" if hero_img else ""}
            <div class="nf-hero-gradient"></div>
            <div class="nf-hero-content">
                <div class="nf-hero-title">{hero_title}</div>
                <div class="nf-hero-meta">
                    <span class="nf-hero-score">▶ {hero_note:.1f}</span>
                    <span class="nf-hero-year">{hero_annee}</span>
                    {plat_html}
                </div>
                <p class="nf-hero-desc">{hero_desc}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Bouton "Plus d'infos" sous le hero ──

        if st.button(f"ℹ️ Plus sur « {hero_title} »", key="hero_detail"):
            st.session_state.film_detail = hero["id"]
            st.rerun()

        # ── Grille 6 colonnes ──
        st.markdown('<div class="nf-section">', unsafe_allow_html=True)
        nb = len(films)
        label_genre = ", ".join(genres_sel) if genres_sel else "Tous genres"
        st.markdown(f'<p class="nf-section-title">Votre sélection <span>{nb} films · {label_genre}</span></p>', unsafe_allow_html=True)

        vus   = vu_ids()
        avoirs = avoir_ids()

        # ── Ligne toggle + Gemini côte à côte ──
        row1, row2, row3 = st.columns([1.5, 3, 1])
        with row1:
            afficher_vus = st.toggle("👁 Afficher les films déjà vus", value=False)
        with row2:
            humeur_input = st.text_input(
                "Envie",
                placeholder="✨ Décrivez votre envie du soir pour une recommandation Gemini…",
                label_visibility="collapsed",
                key="gemini_input"
            )
        with row3:
            demander_gemini = st.button("✨ Gemini", use_container_width=True, key="btn_gemini")

        if demander_gemini:
            if not humeur_input:
                st.warning("Décrivez votre envie pour obtenir une recommandation.")
            elif not GROQ_API_KEY:
                st.warning("⚠️ Clé API Groq manquante — créez un compte gratuit sur groq.com et ajoutez `GROQ_API_KEY` dans vos secrets Streamlit.")
            else:
                with st.spinner("Gemini réfléchit…"):
                    rep = recommander_par_humeur(humeur_input, st.session_state.films_ok)
                st.markdown(f'<div class="nf-ai-box">{rep.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

        films_affiches = films if afficher_vus else [f for f in films if str(f["id"]) not in vus]

        # Nombre de films visibles (pagination)
        for i in range(0, len(films_affiches), 6):
            cols = st.columns(6, gap="small")
            for j, film in enumerate(films_affiches[i:i+6]):
                with cols[j]:
                    render_card(film, prefix="g")
    
    else:
        # État vide
        st.markdown("""
        <div style="text-align:center;padding:6rem 0;">
            <div style="font-size:4rem;margin-bottom:1rem;">🎬</div>
            <p style="font-family:'Bebas Neue',sans-serif;font-size:2rem;color:#fff;margin-bottom:.8rem;">Bonsoir Mr Marc</p>
            <p style="color:#555;font-size:.95rem;line-height:1.8;">
                Choisissez vos critères ci-dessus<br>
                et cliquez sur <strong style="color:#e50914;">▶ Lancer</strong> pour afficher le catalogue.
            </p>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  TAB 2 — RECHERCHE PAR NOM
# ══════════════════════════════════════════════
with tab_search:

    st.markdown('<p style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;color:#fff;margin-bottom:4px;">Rechercher un film</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#666;font-size:.88rem;margin-bottom:16px;">Titre en français ou en anglais — base mondiale TMDB</p>', unsafe_allow_html=True)

    sc1, sc2 = st.columns([5, 1])
    with sc1:
        query = st.text_input("Recherche", placeholder="Ex : Parasite, Inception, Le Fabuleux Destin…", label_visibility="collapsed")
    with sc2:
        chercher = st.button("🔍 Chercher", use_container_width=True)

    if chercher and query:
        with st.spinner("Recherche…"):
            st.session_state.search_results = rechercher_par_nom(query)
            st.session_state.search_query   = query
            st.session_state.search_detail  = None

    # Détail depuis recherche
    if st.session_state.search_detail:
        render_detail(st.session_state.search_detail)
    elif st.session_state.search_results:
        q   = st.session_state.search_query or ""
        res = st.session_state.search_results
        st.markdown(f'<p style="color:#666;font-size:.8rem;margin:12px 0;">{len(res)} résultat{"s" if len(res)>1 else ""} pour « {q} »</p>', unsafe_allow_html=True)

        vus   = vu_ids()
        avoirs = avoir_ids()

        for film in res:
            fid    = film["id"]
            titre  = film.get("title", "?")
            annee  = film.get("release_date", "")[:4] or "—"
            note   = film.get("vote_average", 0)
            poster = film.get("poster_path")
            overview = (film.get("overview") or "Pas de synopsis.")[:160] + "…"
            deja_vu    = str(fid) in vus
            deja_avoir = str(fid) in avoirs

            badge_vu    = '<span class="nf-badge-vu" style="font-size:.6rem;">VU</span>'         if deja_vu    else ""
            badge_avoir = '<span class="nf-badge-avoir" style="font-size:.6rem;">À VOIR</span>'  if deja_avoir else ""

            col_img, col_info = st.columns([1, 5])
            with col_img:
                if poster:
                    st.image(f"https://image.tmdb.org/t/p/w185{poster}", width=70)
                else:
                    st.markdown("🎬")
            with col_info:
                st.markdown(f"""
                <div style="padding:4px 0 2px;">
                    <span class="nf-list-title">{titre}</span> {badge_vu}{badge_avoir}
                </div>
                <div style="display:flex;gap:10px;align-items:center;margin-bottom:4px;">
                    <span style="color:#46d369;font-size:.78rem;font-weight:700;">▶ {note:.1f}</span>
                    <span style="color:#777;font-size:.75rem;">{annee}</span>
                </div>
                <p style="color:#888;font-size:.78rem;line-height:1.5;margin:0 0 8px 0;">{overview}</p>
                """, unsafe_allow_html=True)

                rc1, rc2, rc3 = st.columns([2, 1, 1])
                with rc1:
                    if st.button("ℹ️ Détails", key=f"sr_det_{fid}", use_container_width=True):
                        st.session_state.search_detail = fid; st.rerun()
                with rc2:
                    if deja_vu:
                        if st.button("↩️ Retirer", key=f"sr_rvu_{fid}", use_container_width=True):
                            vu_retirer(fid); st.rerun()
                    else:
                        if st.button("👁 VU", key=f"sr_vu_{fid}", use_container_width=True):
                            vu_ajouter(fid, titre, annee); avoir_retirer(fid); st.rerun()
                with rc3:
                    if deja_avoir:
                        if st.button("↩️ Retirer", key=f"sr_rav_{fid}", use_container_width=True):
                            avoir_retirer(fid); st.rerun()
                    elif not deja_vu:
                        if st.button("🔖 À voir", key=f"sr_av_{fid}", use_container_width=True):
                            avoir_ajouter(fid, titre, annee); st.rerun()

            st.divider()

    elif not chercher:
        st.markdown("""
        <div style="text-align:center;padding:4rem 0;">
            <div style="font-size:3rem;margin-bottom:1rem;">🔍</div>
            <p style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;color:#fff;margin-bottom:.6rem;">Trouvez n'importe quel film</p>
            <p style="color:#555;font-size:.88rem;">Recherchez par titre, ajoutez-le à votre liste ou marquez-le comme vu.</p>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  TAB 3 — À VOIR
# ══════════════════════════════════════════════
with tab_avoir:

    avoir_data = avoir_charger()

    st.markdown('<p style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;color:#fff;margin-bottom:16px;">Ma liste À Voir</p>', unsafe_allow_html=True)

    if not avoir_data:
        st.markdown("""
        <div style="text-align:center;padding:4rem 0;">
            <div style="font-size:3rem;margin-bottom:1rem;">🔖</div>
            <p style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;color:#fff;margin-bottom:.6rem;">Votre liste est vide</p>
            <p style="color:#555;font-size:.88rem;">Ajoutez des films depuis le Catalogue ou la Recherche.</p>
        </div>""", unsafe_allow_html=True)
    else:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Films à voir", len(avoir_data))

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        # Grille 6 colonnes avec jaquettes
        ids_list = list(avoir_data.items())
        for i in range(0, len(ids_list), 6):
            cols = st.columns(6, gap="small")
            for j, (fid, info) in enumerate(ids_list[i:i+6]):
                with cols[j]:
                    titre     = info.get("titre", "?")
                    annee     = info.get("annee", "?")
                    date_ajout = info.get("date", "—")
                    poster_path, _, note, _, _ = get_poster_note(int(fid))

                    img_src_av = f"https://image.tmdb.org/t/p/w300{poster_path}" if poster_path else ""
                    img_av = (f'<img src="{img_src_av}" alt="{titre}" loading="lazy">'
                              if img_src_av else '<div class="nf-card-img-ph">🎬</div>')

                    st.markdown(f"""
                    <div class="nf-card-container">
                        <div class="nf-card-img-wrap">
                            {img_av}
                            <div class="nf-card-play">&#9654;</div>
                            <div class="nf-card-badges">
                                <span class="nf-badge-avoir">À VOIR</span>
                            </div>
                            <div class="nf-card-overlay">
                                <div class="nf-card-title">{titre}</div>
                                <div class="nf-card-meta">
                                    <span class="nf-card-score">&#9654; {note:.1f}</span>
                                    <span class="nf-card-year">{annee}</span>
                                </div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    if st.button("▶ Détails", key=f"av_det_{fid}", use_container_width=True):
                        st.session_state.film_detail = int(fid); st.rerun()
            
                    ba1, ba2 = st.columns(2)
                    with ba1:
                        if st.button("✅ VU", key=f"av_vu_{fid}", use_container_width=True, help="Marquer vu"):
                            vu_ajouter(int(fid), titre, annee); avoir_retirer(int(fid)); st.rerun()
                    with ba2:
                        if st.button("🗑 Retirer", key=f"av_del_{fid}", use_container_width=True, help="Retirer"):
                            avoir_retirer(int(fid)); st.rerun()


# ══════════════════════════════════════════════
#  TAB 5 — FILMS VUS
# ══════════════════════════════════════════════
with tab_vus:

    vus_data = vu_charger()

    st.markdown('<p style="font-family:\'Bebas Neue\',sans-serif;font-size:2rem;color:#fff;margin-bottom:16px;">Mes films vus</p>', unsafe_allow_html=True)

    if not vus_data:
        st.markdown("""
        <div style="text-align:center;padding:4rem 0;">
            <div style="font-size:3rem;margin-bottom:1rem;">✅</div>
            <p style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;color:#fff;margin-bottom:.6rem;">Aucun film marqué</p>
            <p style="color:#555;font-size:.88rem;">Marquez vos films comme vus depuis les détails ou la recherche.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.metric("Films vus", len(vus_data))
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        for fid, info in sorted(vus_data.items(), key=lambda x: x[1].get("date",""), reverse=True):
            titre  = info.get("titre", "?")
            annee  = info.get("annee", "?")
            date_v = info.get("date", "—")
            poster_path, _, note, _, _ = get_poster_note(int(fid))

            img_html = (f'<img class="nf-list-thumb" src="https://image.tmdb.org/t/p/w185{poster_path}" alt="{titre}">'
                        if poster_path else '<div class="nf-list-ph">🎬</div>')

            st.markdown(f"""
            <div class="nf-list-item">
                {img_html}
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <span class="nf-list-title">{titre}</span>
                        <span class="nf-badge-vu">VU</span>
                    </div>
                    <span style="color:#777;font-size:.75rem;">{annee} · vu le {date_v}</span>
                </div>
            </div>""", unsafe_allow_html=True)

            if st.button("🗑 Retirer", key=f"vus_del_{fid}"):
                vu_retirer(fid); st.rerun()

