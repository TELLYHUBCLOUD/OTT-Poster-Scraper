import urllib.parse
import re
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from auth import verify_token

router = APIRouter()

from adult.iafd import iafd, search_iafd
from adult.theporndb import theporndb, search_theporndb
from adult.afd import afd, search_afd
from adult.stashbox import stashbox, search_stashbox
from adult.prdb import prdb, search_prdb

def handle_adult_response(res):
    if isinstance(res, dict):
        if "error" in res:
            return JSONResponse(content=res, status_code=400)
        return JSONResponse(content=res, status_code=200)
    elif res is None:
        return JSONResponse(content={"error": "Adult database scraper returned empty result"}, status_code=400)
    else:
        return JSONResponse(content=res, status_code=200)

@router.get("/url")
def adult_url(url: str = Query(..., description="Content URL from IAFD, ThePornDB, AFD, Stash-box, or PRDB")):
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()

    try:
        if "iafd.com" in domain:
            return handle_adult_response(iafd(url))
        elif "theporndb.net" in domain:
            return handle_adult_response(theporndb(url))
        elif "adultfilmdatabase.com" in domain:
            return handle_adult_response(afd(url))
        elif "stashdb.org" in domain:
            return handle_adult_response(stashbox(url))
        elif "prdb.net" in domain:
            return handle_adult_response(prdb(url))
        else:
            return JSONResponse(content={"error": f"Unsupported adult database domain: {domain}"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"Adult URL routing failed: {str(e)}"}, status_code=500)

@router.get("/title")
def adult_title(
    title: str = Query(..., description="Scene or movie title to search"),
    site: str = Query("iafd", description="Database site to search on: iafd, theporndb, afd, stashbox, prdb")
):
    site_lower = site.lower().strip()

    try:
        if site_lower == "iafd":
            return handle_adult_response(search_iafd(title))
        elif site_lower == "theporndb":
            return handle_adult_response(search_theporndb(title))
        elif site_lower == "afd":
            return handle_adult_response(search_afd(title))
        elif site_lower == "stashbox":
            return handle_adult_response(search_stashbox(title))
        elif site_lower == "prdb":
            return handle_adult_response(search_prdb(title))
        else:
            return JSONResponse(content={"error": f"Unsupported adult search database: {site}"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"Adult title search routing failed: {str(e)}"}, status_code=500)
