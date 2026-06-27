import re
from curl_cffi import requests
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()

BASE_IMAGE_CDN = "https://img1.hotstarext.com/image/upload/f_auto"

def extract_hotstar_id(url: str) -> str:
    url_clean = url.split("?")[0].split("#")[0].strip("/")
    parts = url_clean.split("/")
    if parts:
        last_part = parts[-1]
        if last_part.isdigit():
            return last_part
        match = re.search(r'(\d+)$', last_part)
        if match:
            return match.group(1)
    return None

def hotstar(url: str):
    content_id = extract_hotstar_id(url)
    if not content_id:
        return {"error": "Invalid Hotstar URL, could not extract content ID"}
        
    api_url = f"https://api.hotstar.com/o/v1/multi/get/content?ids={content_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-country-code": "IN",
        "x-platform-code": "web",
    }
    
    try:
        r = requests.get(api_url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"Failed to fetch data from Hotstar API (Status Code: {r.status_code})"}
            
        data = r.json()
        results = data.get("body", {}).get("results", {}).get("map", {})
        if not results or content_id not in results:
            return {"error": "No metadata found for this content ID on Hotstar"}
            
        content = results[content_id]
        title = content.get("title", "Unknown")
        year = content.get("year")
        
        display_title = f"{title} - ({year})" if year else title
        
        images = content.get("images", {})
        landscape = f"{BASE_IMAGE_CDN}/{images.get('h')}" if images.get('h') else None
        portrait = f"{BASE_IMAGE_CDN}/{images.get('v')}" if images.get('v') else None
        cover = f"{BASE_IMAGE_CDN}/{images.get('b')}" if images.get('b') else None
        logo = f"{BASE_IMAGE_CDN}/{images.get('t')}" if images.get('t') else None
        banner = f"{BASE_IMAGE_CDN}/{images.get('m')}" if images.get('m') else None
        
        return {
            "title": display_title,
            "landscape": landscape,
            "portrait": portrait,
            "cover": cover,
            "logo": logo,
            "banner": banner
        }
    except Exception as e:
        return {"error": f"An error occurred during scraping: {str(e)}"}

@router.get("/hotstar")
def hotstar_poster(url: str = Query(..., description="Hotstar content URL")):
    result = hotstar(url)
    if "error" in result:
        return JSONResponse(content=result, status_code=400)
    return JSONResponse(content=result, status_code=200)
