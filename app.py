import os
from pathlib import Path

import requests
from flask import Flask, render_template, request, session, redirect, url_for

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

# Oturumda dil tercihi tutmak için bir secret key gerekiyor.
# Vercel'de bunu da bir ortam değişkeni olarak (FLASK_SECRET_KEY) verebilirsin,
# vermezsen aşağıdaki sabit değer kullanılır (küçük bir proje için sorun değil).
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "which-movie-dev-secret")

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w342"

SUPPORTED_LANGS = ["tr", "en", "ru"]
DEFAULT_LANG = "tr"

# TMDB'nin kendi dil kodları (sonuçların özet/başlık dilini belirler)
TMDB_LANG_CODES = {"tr": "tr-TR", "en": "en-US", "ru": "ru-RU"}

TRANSLATIONS = {
    "tr": {
        "site_title": "WHICH MOVIE?",
        "site_tagline": "bir isim ver, aynı raftan sana öner",
        "ticket_label": "İZLEDİĞİN / SEVDİĞİN YAPIM",
        "placeholder": "Örn: Breaking Bad, Inception, Dark...",
        "search_button": "Öneri Bul",
        "found_eyebrow": "Bulunan",
        "reel_heading": "— Aynı Kategoriden Öneriler —",
        "footer_note": "Veriler TMDB'den gelir, bu ürün TMDB tarafından onaylanmamıştır.",
        "movie_label": "Film",
        "tv_label": "Dizi",
        "no_overview": "Bu içerik için özet bulunmuyor.",
        "err_no_key": "TMDB_API_KEY tanımlı değil. Lütfen ortam değişkenlerini kontrol et.",
        "err_empty_query": "Lütfen bir dizi ya da film ismi yaz.",
        "err_not_found": '"{query}" için bir sonuç bulamadım. Yazımı kontrol eder misin?',
        "err_no_recs": "Aynı kategoride başka önerim çıkmadı, farklı bir şey dene.",
        "err_request": "TMDB'ye ulaşırken bir sorun oldu, birazdan tekrar dene.",
        "theme_toggle": "Tema",
        "close_label": "Kapat",
        "read_more": "Devamını oku",
    },
    "en": {
        "site_title": "WHICH MOVIE?",
        "site_tagline": "give a title, get matches from the same shelf",
        "ticket_label": "SOMETHING YOU WATCHED / LOVED",
        "placeholder": "e.g. Breaking Bad, Inception, Dark...",
        "search_button": "Find Matches",
        "found_eyebrow": "Found",
        "reel_heading": "— More From The Same Category —",
        "footer_note": "Data comes from TMDB. This product is not endorsed by TMDB.",
        "movie_label": "Movie",
        "tv_label": "TV Show",
        "no_overview": "No overview available for this title.",
        "err_no_key": "TMDB_API_KEY is not set. Please check your environment variables.",
        "err_empty_query": "Please enter a movie or show title.",
        "err_not_found": 'No results for "{query}". Double-check the spelling?',
        "err_no_recs": "Couldn't find more in the same category, try something else.",
        "err_request": "Had trouble reaching TMDB, try again in a moment.",
        "theme_toggle": "Theme",
        "close_label": "Close",
        "read_more": "Read more",
    },
    "ru": {
        "site_title": "WHICH MOVIE?",
        "site_tagline": "назови тайтл — подберём похожее с той же полки",
        "ticket_label": "ЧТО ТЫ СМОТРЕЛ(-А) / ПОЛЮБИЛ(-А)",
        "placeholder": "напр. Breaking Bad, Inception, Dark...",
        "search_button": "Найти похожее",
        "found_eyebrow": "Найдено",
        "reel_heading": "— Ещё из той же категории —",
        "footer_note": "Данные предоставлены TMDB. Продукт не одобрен TMDB.",
        "movie_label": "Фильм",
        "tv_label": "Сериал",
        "no_overview": "Для этого тайтла нет описания.",
        "err_no_key": "TMDB_API_KEY не задан. Проверь переменные окружения.",
        "err_empty_query": "Введите название фильма или сериала.",
        "err_not_found": 'Ничего не нашлось по запросу "{query}". Проверь написание.',
        "err_no_recs": "Больше похожего в этой категории не нашлось, попробуй другой тайтл.",
        "err_request": "Не удалось связаться с TMDB, попробуй ещё раз через момент.",
        "theme_toggle": "Тема",
        "close_label": "Закрыть",
        "read_more": "Читать дальше",
    },
}


def get_lang():
    lang = session.get("lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def tmdb_get(path, params=None, lang="tr"):
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    params["language"] = TMDB_LANG_CODES.get(lang, "tr-TR")
    response = requests.get(f"{TMDB_BASE_URL}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def search_title(query, lang):
    data = tmdb_get("/search/multi", {"query": query, "include_adult": "false"}, lang=lang)
    results = [
        r for r in data.get("results", [])
        if r.get("media_type") in ("movie", "tv") and r.get("genre_ids")
    ]
    if not results:
        return None
    results.sort(key=lambda r: r.get("popularity", 0), reverse=True)
    return results[0]


def get_genre_names(media_type, lang):
    data = tmdb_get(f"/genre/{media_type}/list", lang=lang)
    return {g["id"]: g["name"] for g in data.get("genres", [])}


def discover_by_genre(media_type, genre_ids, exclude_id, lang):
    data = tmdb_get(
        f"/discover/{media_type}",
        {
            "with_genres": ",".join(str(g) for g in genre_ids[:2]),
            "sort_by": "popularity.desc",
            "vote_count.gte": 50,
        },
        lang=lang,
    )
    items = [r for r in data.get("results", []) if r["id"] != exclude_id]
    return items[:12]


def get_similar_titles(media_type, item_id, lang):
    """TMDB'nin kendi öğrenilmiş benzerlik motorunu kullanır (sadece tür eşleşmesinden
    daha isabetli sonuçlar verir)."""
    data = tmdb_get(f"/{media_type}/{item_id}/recommendations", lang=lang)
    return data.get("results", [])


def build_recommendations(media_type, found, lang, limit=12):
    """Önce TMDB'nin benzerlik motorundan, yetmezse aynı türdeki popüler
    içeriklerden doldurarak tekrarsız bir öneri listesi oluşturur."""
    seen_ids = {found["id"]}
    combined = []

    for item in get_similar_titles(media_type, found["id"], lang):
        if item["id"] not in seen_ids:
            combined.append(item)
            seen_ids.add(item["id"])
        if len(combined) >= limit:
            break

    if len(combined) < limit:
        for item in discover_by_genre(media_type, found.get("genre_ids", []), found["id"], lang):
            if item["id"] not in seen_ids:
                combined.append(item)
                seen_ids.add(item["id"])
            if len(combined) >= limit:
                break

    return combined[:limit]


def format_item(item, media_type_fallback, genre_lookup, t):
    media_type = item.get("media_type", media_type_fallback)
    title = item.get("title") or item.get("name") or "—"
    date = item.get("release_date") or item.get("first_air_date") or ""
    year = date[:4] if date else "—"
    poster_path = item.get("poster_path")
    genres = [genre_lookup.get(gid, "") for gid in item.get("genre_ids", [])]
    genres = [g for g in genres if g][:3]
    return {
        "title": title,
        "year": year,
        "overview": item.get("overview") or t["no_overview"],
        "poster": f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None,
        "rating": round(item.get("vote_average", 0), 1),
        "media_type": t["tv_label"] if media_type == "tv" else t["movie_label"],
        "genres": genres,
    }


@app.route("/set-lang/<lang_code>", methods=["POST"])
def set_lang(lang_code):
    if lang_code in SUPPORTED_LANGS:
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    lang = get_lang()
    t = TRANSLATIONS[lang]

    context = {
        "query": "",
        "error": None,
        "source": None,
        "recommendations": [],
        "t": t,
        "lang": lang,
        "supported_langs": SUPPORTED_LANGS,
    }

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        context["query"] = query

        if not TMDB_API_KEY:
            context["error"] = t["err_no_key"]
            return render_template("index.html", **context)

        if not query:
            context["error"] = t["err_empty_query"]
            return render_template("index.html", **context)

        try:
            found = search_title(query, lang)
            if not found:
                context["error"] = t["err_not_found"].format(query=query)
                return render_template("index.html", **context)

            media_type = found["media_type"]
            genre_lookup = get_genre_names(media_type, lang)

            context["source"] = format_item(found, media_type, genre_lookup, t)

            raw_recs = build_recommendations(media_type, found, lang)
            context["recommendations"] = [
                format_item(r, media_type, genre_lookup, t) for r in raw_recs
            ]

            if not context["recommendations"]:
                context["error"] = t["err_no_recs"]

        except requests.exceptions.RequestException:
            context["error"] = t["err_request"]

    return render_template("index.html", **context)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
