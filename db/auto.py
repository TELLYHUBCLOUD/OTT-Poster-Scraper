import urllib.parse
import json
import re
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()

# Scraper imports
from db.imdb import imdb, search_imdb
from db.tmdb import tmdb, search_tmdb
from db.tvdb import tvdb
from db.mydramalist import mydramalist, search_mydramalist
from db.anilist import anilist, search_anilist
from db.kitsu import kitsu, search_kitsu
from db.tvmaze import tvmaze, search_tvmaze
from db.letterboxd import letterboxd, search_letterboxd

def parse_season_episode(query: str):
    patterns = [
        r'(.*?)\s+s(?:eason)?\s*(\d+)\s*e(?:p(?:isode)?)?\s*(\d+)', # Title S01E02, Title Season 1 Episode 2, Title S1 Ep2
        r'(.*?)\s+(\d+)x(\d+)', # Title 1x02
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            clean_title = match.group(1).strip()
            season = int(match.group(2))
            episode = int(match.group(3))
            return clean_title, season, episode
            
    return query.strip(), None, None

def handle_db_response(res):
    if isinstance(res, dict):
        if "error" in res:
            return JSONResponse(content=res, status_code=400)
        return JSONResponse(content=res, status_code=200)
    elif res is None:
        return JSONResponse(content={"error": "Database scraper returned empty result"}, status_code=400)
    else:
        return JSONResponse(content=res, status_code=200)

@router.get("/url")
def db_url(url: str = Query(..., description="Content URL from IMDb, TMDB, TVDB, MyDramaList, AniList, Kitsu, TVmaze, or Letterboxd")):
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    
    try:
        if "imdb.com" in domain:
            return handle_db_response(imdb(url))
        elif "themoviedb.org" in domain:
            return handle_db_response(tmdb(url))
        elif "thetvdb.com" in domain:
            return handle_db_response(tvdb(url))
        elif "mydramalist.com" in domain:
            return handle_db_response(mydramalist(url))
        elif "anilist.co" in domain:
            return handle_db_response(anilist(url))
        elif "kitsu.io" in domain:
            return handle_db_response(kitsu(url))
        elif "tvmaze.com" in domain:
            return handle_db_response(tvmaze(url))
        elif "letterboxd.com" in domain:
            return handle_db_response(letterboxd(url))
        else:
            return JSONResponse(content={"error": f"Unsupported database platform or domain: {domain}"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"Database URL routing failed: {str(e)}"}, status_code=500)

@router.get("/title")
def db_title(
    title: str = Query(..., description="Movie, series, or anime title. Will automatically detect season/episode details (e.g. S01E02)"),
    site: str = Query("tmdb", description="Database site to search on: tmdb, imdb, tvmaze, mydramalist, anilist, kitsu, letterboxd")
):
    clean_title, season, episode = parse_season_episode(title)
    site_lower = site.lower().strip()
    
    try:
        if site_lower == "tmdb":
            return handle_db_response(search_tmdb(clean_title, season, episode))
        elif site_lower == "imdb":
            return handle_db_response(search_imdb(clean_title, season, episode))
        elif site_lower == "tvmaze":
            return handle_db_response(search_tvmaze(clean_title, season, episode))
        elif site_lower == "mydramalist":
            return handle_db_response(search_mydramalist(clean_title))
        elif site_lower == "anilist":
            return handle_db_response(search_anilist(clean_title))
        elif site_lower == "kitsu":
            return handle_db_response(search_kitsu(clean_title))
        elif site_lower == "letterboxd":
            return handle_db_response(search_letterboxd(clean_title))
        else:
            return JSONResponse(content={"error": f"Unsupported search database: {site}"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"Database title search routing failed: {str(e)}"}, status_code=500)
