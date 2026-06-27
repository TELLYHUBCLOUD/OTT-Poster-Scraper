import urllib.parse
import json
import re
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()

# Static imports from existing modules
from posters.aaonxt import fetch_aaonxt
from posters.addatimes import fetch_addatimes
from posters.aha import aha
from posters.airtel import airtel
from posters.amz import amazon
from posters.appletv import apple
from posters.atrangii import atrangii
from posters.bms import bms
from posters.chaupal import chaupal
from posters.crunchyroll import crunchyroll_poster
from posters.dangal import dangalplay
from posters.eros import erosnow
from posters.hoichoi import hoichoi_scraper, clean_hoichoi_url
from posters.hulu import scrape_hulu_images
from posters.hungama import fetch_hungama
from posters.iqyi import iq
from posters.jojo import jojo_poster
from posters.lionsgate import lionsgate
from posters.mubi import mubi
from posters.mxplayer import mxplayer
from posters.nf import fetch_netflix_metadata
from posters.playflix import playflix
from posters.plextv import plex
from posters.sainaplay import sainaplay_poster
from posters.shemaroo import shemaroo
from posters.sonyliv import sonyliv_poster
from posters.sunnxt import sunnxt
from posters.tataplay import tataplay
from posters.ticketnew import scrape_ticketnew_movie
from posters.tubi import tubi_poster
from posters.ultra import ultra
from posters.ultrajhakaas import ultrajhakaas_poster
from posters.viki import viki
from posters.viu import viu_poster
from posters.vivamax import vivamax
from posters.wetv import wetv
from posters.youku import youku
from posters.yt import youtube
from posters.zee5 import scrape_zee5_meta
from posters.hotstar import hotstar

def handle_response(res):
    if isinstance(res, JSONResponse):
        try:
            content = json.loads(res.body.decode("utf-8"))
            return JSONResponse(content=content, status_code=res.status_code)
        except Exception:
            return JSONResponse(content={"error": "Failed to decode target response"}, status_code=500)
    elif isinstance(res, dict):
        if "error" in res:
            return JSONResponse(content=res, status_code=400)
        return JSONResponse(content=res, status_code=200)
    elif isinstance(res, tuple):
        return JSONResponse(content={"data": res}, status_code=200)
    elif res is None:
        return JSONResponse(content={"error": "Failed to extract poster: Scraper returned None"}, status_code=400)
    else:
        return JSONResponse(content=res, status_code=200)

@router.get("/auto")
def auto_detect_poster(url: str = Query(..., description="Content URL from any supported OTT platform")):
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    
    try:
        if "aaonxt.com" in domain:
            return handle_response(fetch_aaonxt(url))
        elif "addatimes.com" in domain:
            return handle_response(fetch_addatimes(url))
        elif "aha.video" in domain:
            return handle_response(aha(url))
        elif "airtel.tv" in domain or "airtelxstream.in" in domain:
            return handle_response(airtel(url))
        elif "amazon." in domain or "primevideo.com" in domain or "amzn.to" in domain:
            return handle_response(amazon(url))
        elif "apple.com" in domain:
            return handle_response(apple(url))
        elif "atrangii." in domain or "atrangi." in domain:
            return handle_response(atrangii(url))
        elif "bookmyshow.com" in domain:
            return handle_response(bms(url))
        elif "chaupal.tv" in domain:
            return handle_response(chaupal(url))
        elif "crunchyroll.com" in domain:
            return handle_response(crunchyroll_poster(url))
        elif "dangallive.com" in domain or "dangalplay.com" in domain:
            parts = url.strip("/").split("/")
            slug = parts[-1]
            slug_type = parts[-2]
            return handle_response(dangalplay(slug, slug_type))
        elif "erosnow.com" in domain:
            return handle_response(erosnow(url))
        elif "hoichoi.tv" in domain:
            return handle_response(hoichoi_scraper(clean_hoichoi_url(url)))
        elif "hulu.com" in domain:
            return handle_response(scrape_hulu_images(url))
        elif "hungama.com" in domain:
            return handle_response(fetch_hungama(url))
        elif "iq.com" in domain or "iqiyi.com" in domain:
            return handle_response(iq(url))
        elif "jojoapp.in" in domain:
            return handle_response(jojo_poster(url))
        elif "lionsgateplay.com" in domain:
            return handle_response(lionsgate(url))
        elif "mubi.com" in domain:
            return handle_response(mubi(url))
        elif "mxplayer.in" in domain:
            return handle_response(mxplayer(url))
        elif "netflix.com" in domain:
            return handle_response(fetch_netflix_metadata(url))
        elif "playflix.app" in domain or "playflix.tv" in domain or "qwilted-cds.cqloud.com" in domain:
            return handle_response(playflix(url))
        elif "plex.tv" in domain:
            return handle_response(plex(url))
        elif "sainaplay.com" in domain:
            return handle_response(sainaplay_poster(url))
        elif "shemaroome.com" in domain or "shemaroo.com" in domain:
            return handle_response(shemaroo(url))
        elif "sonyliv.com" in domain:
            return handle_response(sonyliv_poster(url))
        elif "sunnxt.com" in domain:
            return handle_response(sunnxt(url))
        elif "tataplay.com" in domain:
            return handle_response(tataplay(url))
        elif "ticketnew.com" in domain:
            return handle_response(scrape_ticketnew_movie(url))
        elif "tubitv.com" in domain:
            return handle_response(tubi_poster(url))
        elif "ultraplay.in" in domain or "ultraplay" in domain or "ultra" in domain:
            return handle_response(ultra(url))
        elif "ultrajhakaas.in" in domain:
            return handle_response(ultrajhakaas_poster(url))
        elif "viki.com" in domain:
            return handle_response(viki(url))
        elif "viu.com" in domain:
            return handle_response(viu_poster(url))
        elif "vivamax.net" in domain or "vivamax.com" in domain:
            return handle_response(vivamax(url))
        elif "wetv.vip" in domain:
            return handle_response(wetv(url))
        elif "youku.tv" in domain or "youku.com" in domain:
            return handle_response(youku(url))
        elif "youtube.com" in domain or "youtu.be" in domain:
            return handle_response(youtube(url))
        elif "zee5.com" in domain:
            return handle_response(scrape_zee5_meta(url))
        elif "hotstar.com" in domain:
            return handle_response(hotstar(url))
        else:
            return JSONResponse(content={"error": f"Unsupported platform or domain: {domain}"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"Auto-detection routing failed: {str(e)}"}, status_code=500)
