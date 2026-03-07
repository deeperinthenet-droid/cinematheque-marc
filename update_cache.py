"""
update_cache.py
───────────────
Télécharge depuis TMDB tous les films disponibles sur les plateformes FR
avec une note ≥ 8.0, et sauvegarde le résultat dans cache_films.json.

Utilisation :
    python update_cache.py --api-key VOTRE_CLE_TMDB
    python update_cache.py  # lit TMDB_API_KEY depuis l'environnement

Lancé automatiquement chaque mois par GitHub Actions (.github/workflows/update_cache.yml)
"""

import requests
import json
import time
import argparse
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# JustWatch via simplejustwatchapi (pip install simplejustwatchapi)
try:
    from simplejustwatchapi.justwatch import search as jw_search
    HAS_JW = True
except ImportError:
    HAS_JW = False
    print("⚠️  simplejustwatchapi non installé — Canal+ enrichi via TMDB uniquement")
    print("   Pour l'activer : pip install simplejustwatchapi\n")

# Correspondances noms JustWatch → noms de l'app
JW_NOMS = {
    "Netflix": "Netflix",
    "Canal+": "Canal+",
    "Canal+ Cinema": "Canal+",
    "CanalPlus": "Canal+",
    "Disney Plus": "Disney+",
    "Disney+": "Disney+",
    "Amazon Prime Video": "Amazon",
    "Amazon Prime Video with Ads": "Amazon",
    "Max": "Max",
    "HBO Max": "Max",
    "Arte": "Arte",
    "France Télévisions": "France TV",
    "France.tv": "France TV",
    "MyTF1": "MyTF1 Max",
    "TF1+": "MyTF1 Max",
    "6play": "6play Max",
    "M6+": "6play Max",
    "OCS": "OCS",
}

# ─── CONFIG ───────────────────────────────────────────────────────────────────

MES_PLATEFORMES = {
    "Netflix": 8, "Canal+": 381, "Disney+": 337, "Amazon": 119,
    "Max": 1899, "Arte": 234, "France TV": 312, "MyTF1 Max": 1870,
    "6play Max": 1866, "OCS": 56,
}

NOTE_MINI     = 7.5
NOTE_MINI_CANAL = 7.5
VOTES_MINI    = 50        # ignorer les films avec trop peu de votes
ANNEE_MINI    = 1930
MAX_PAGES     = 10        # 10 pages × 20 films = 200 films par plateforme max
MAX_WORKERS   = 12
OUTPUT_FILE   = "cache_films.json"

BASE_URL = "https://api.themoviedb.org/3"

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get(path, params, api_key, retries=3):
    params["api_key"] = api_key
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 5))
                print(f"  Rate limit, attente {wait}s…")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ⚠️  Erreur {path} : {e}")
                return None
            time.sleep(1)
    return None


def fetch_providers_justwatch(titre: str, annee: str) -> list:
    """Cherche les plateformes FR via JustWatch (plus complet que TMDB pour Canal+)."""
    if not HAS_JW:
        return []
    try:
        resultats = jw_search(titre, "FR", "fr", 3, True)
        if not resultats:
            return []
        for item in resultats[:5]:
            item_titre = (item.title or "").lower()
            # Correspondance approximative du titre
            if titre.lower()[:8] in item_titre or item_titre[:8] in titre.lower():
                offres = []
                for offer in (item.offers or []):
                    if offer.monetization_type == "FLATRATE":
                        nom_jw  = offer.package.name if offer.package else ""
                        nom_app = JW_NOMS.get(nom_jw)
                        if nom_app and nom_app in MES_PLATEFORMES and nom_app not in offres:
                            offres.append(nom_app)
                if offres:
                    return offres
        return []
    except Exception:
        return []


def fetch_providers(movie_id, api_key, titre="", annee=""):
    """Retourne la liste des plateformes FR — TMDB + JustWatch fusionnés."""
    # TMDB
    data = get(f"/movie/{movie_id}/watch/providers", {}, api_key)
    tmdb_offres = []
    if data:
        results = data.get("results", {}).get("FR", {})
        flat = results.get("flatrate", []) + results.get("free", []) + results.get("ads", [])
        tmdb_offres = [p["provider_name"] for p in flat if p["provider_name"] in MES_PLATEFORMES]

    # JustWatch (surtout utile pour Canal+)
    jw_offres = fetch_providers_justwatch(titre, annee) if titre else []

    # Fusion sans doublons
    union = list(dict.fromkeys(tmdb_offres + [p for p in jw_offres if p not in tmdb_offres]))
    return union


def fetch_details(movie_id, api_key):
    """Retourne les détails complets d'un film."""
    data = get(f"/movie/{movie_id}", {
        "language": "fr-FR",
        "append_to_response": "credits,videos,keywords"
    }, api_key)
    return data


def enrich_film(film, api_key):
    """Enrichit un film avec providers (TMDB + JustWatch) + détails."""
    fid   = film["id"]
    titre = film.get("title", "")
    annee = film.get("release_date", "")[:4]

    offres  = fetch_providers(fid, api_key, titre, annee)
    details = fetch_details(fid, api_key)

    if details:
        # Extraire uniquement le trailer YouTube
        videos = details.get("videos", {}).get("results", [])
        trailer = next((v["key"] for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)

        # Extraire réalisateur + 6 premiers acteurs seulement
        crew = details.get("credits", {}).get("crew", [])
        cast = details.get("credits", {}).get("cast", [])[:6]
        directors = [c["name"] for c in crew if c.get("job") == "Director"][:2]
        cast_names = [a["name"] for a in cast]

        film["runtime"]       = details.get("runtime", 0)
        film["genres"]        = [{"id": g["id"], "name": g["name"]} for g in details.get("genres", [])]
        film["tagline"]       = details.get("tagline", "")
        film["trailer_key"]   = trailer
        film["directors"]     = directors
        film["cast"]          = cast_names
        film["backdrop_path"] = details.get("backdrop_path", film.get("backdrop_path"))
        film["overview"]      = details.get("overview", film.get("overview", ""))

        # Supprimer les champs lourds non nécessaires
        film.pop("credits", None)
        film.pop("videos", None)

    film["offres"] = offres
    return film


# ─── FETCH CATALOGUE ──────────────────────────────────────────────────────────

def fetch_films_for_platform(provider_id, provider_name, api_key):
    """Récupère tous les films pour une plateforme donnée."""
    note = NOTE_MINI_CANAL if provider_name == "Canal+" else NOTE_MINI
    films = []
    seen  = set()

    for page in range(1, MAX_PAGES + 1):
        data = get("/discover/movie", {
            "language":                "fr-FR",
            "region":                  "FR",
            "watch_region":            "FR",
            "with_watch_providers":    provider_id,
            "watch_monetization_types":"flatrate|free|ads",
            "vote_average.gte":        note,
            "vote_count.gte":          VOTES_MINI,
            "primary_release_date.gte":f"{ANNEE_MINI}-01-01",
            "sort_by":                 "vote_average.desc",
            "page":                    page,
        }, api_key)

        if not data or not data.get("results"):
            break

        for f in data["results"]:
            if f["id"] not in seen:
                seen.add(f["id"])
                films.append(f)

        total_pages = data.get("total_pages", 1)
        print(f"  {provider_name} — page {page}/{min(total_pages, MAX_PAGES)} ({len(films)} films)")

        if page >= total_pages:
            break

        time.sleep(0.25)  # respecter le rate limit TMDB

    return films


def build_cache(api_key):
    print(f"\n{'='*60}")
    print(f"  Cinémathèque Mr Marc — Mise à jour du cache")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*60}\n")

    # 1. Collecter tous les films bruts par plateforme
    all_films = {}  # id → film

    for name, pid in MES_PLATEFORMES.items():
        print(f"\n📡 Récupération {name} (provider_id={pid})…")
        films = fetch_films_for_platform(pid, name, api_key)
        for f in films:
            if f["id"] not in all_films:
                all_films[f["id"]] = f

    print(f"\n✅ {len(all_films)} films uniques trouvés avant enrichissement\n")

    # 2. Enrichir en parallèle (providers + détails)
    films_list  = list(all_films.values())
    enriched    = []
    total       = len(films_list)
    done        = 0

    print(f"🔄 Enrichissement de {total} films ({MAX_WORKERS} workers)…\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(enrich_film, f, api_key): f for f in films_list}
        for future in as_completed(futures):
            result = future.result()
            if result and result.get("offres"):  # garder seulement si dispo sur une plateforme FR
                enriched.append(result)
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{total} enrichis ({len(enriched)} avec offres FR)…")

    # 3. Trier par note décroissante
    enriched.sort(key=lambda f: f.get("vote_average", 0), reverse=True)

    # 4. Sauvegarder
    cache = {
        "updated_at": datetime.now().isoformat(),
        "total":      len(enriched),
        "films":      enriched,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fp:
        json.dump(cache, fp, ensure_ascii=False, indent=2)

    size_mb = os.path.getsize(OUTPUT_FILE) / 1_000_000
    print(f"\n{'='*60}")
    print(f"  ✅ Cache sauvegardé : {OUTPUT_FILE}")
    print(f"  📊 {len(enriched)} films | {size_mb:.1f} MB")
    print(f"  🕐 Mis à jour le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    print(f"{'='*60}\n")

    return len(enriched)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Met à jour le cache TMDB pour Cinémathèque Mr Marc")
    parser.add_argument("--api-key", help="Clé API TMDB (sinon lit TMDB_API_KEY depuis l'env)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("TMDB_API_KEY", "")
    if not api_key:
        print("❌ Clé API TMDB manquante. Utilisez --api-key ou la variable d'env TMDB_API_KEY")
        sys.exit(1)

    count = build_cache(api_key)
    print(f"Terminé — {count} films dans le cache.")
