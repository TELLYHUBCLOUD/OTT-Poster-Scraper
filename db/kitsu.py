import re
import urllib.parse
from curl_cffi import requests

KITSU_API_URL = "https://kitsu.io/api/edge/anime"

def extract_kitsu_id_or_slug(url: str) -> tuple:
    # Match standard patterns like kitsu.io/anime/123 or kitsu.io/anime/slug
    url_clean = url.split("?")[0].split("#")[0].strip("/")
    match = re.search(r'kitsu\.io/anime/([a-zA-Z0-9-]+)', url_clean)
    if match:
        val = match.group(1)
        if val.isdigit():
            return int(val), None
        return None, val
    return None, None

def query_kitsu_api(api_url: str) -> dict:
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code != 200:
            return {"error": f"Kitsu API returned status code {r.status_code}"}
        return r.json()
    except Exception as e:
        return {"error": f"Kitsu API request failed: {str(e)}"}

def extract_kitsu_media_details(data_item: dict) -> dict:
    if not data_item:
        return {"error": "No media data found"}
        
    attributes = data_item.get("attributes", {})
    titles = attributes.get("titles", {})
    title = titles.get("en") or titles.get("en_jp") or attributes.get("canonicalTitle") or "Unknown"
    
    start_date = attributes.get("startDate", "")
    year = start_date[:4] if start_date else ""
    display_title = f"{title} - ({year})" if year else title
    
    poster_image = attributes.get("posterImage") or {}
    portrait = poster_image.get("original") or poster_image.get("large")
    
    cover_image = attributes.get("coverImage") or {}
    landscape = cover_image.get("original") or cover_image.get("large") or portrait
    
    return {
        "title": display_title,
        "portrait": portrait,
        "landscape": landscape,
        "description": attributes.get("synopsis", "")
    }

def kitsu(url: str) -> dict:
    k_id, slug = extract_kitsu_id_or_slug(url)
    if not k_id and not slug:
        return {"error": "Invalid Kitsu URL, could not extract ID or slug"}
        
    if k_id:
        api_url = f"{KITSU_API_URL}/{k_id}"
        res_data = query_kitsu_api(api_url)
        if "error" in res_data:
            return res_data
        return extract_kitsu_media_details(res_data.get("data", {}))
    else:
        api_url = f"{KITSU_API_URL}?filter[slug]={slug}"
        res_data = query_kitsu_api(api_url)
        if "error" in res_data:
            return res_data
        data_list = res_data.get("data", [])
        if not data_list:
            return {"error": f"No Kitsu media found matching slug: {slug}"}
        return extract_kitsu_media_details(data_list[0])

def search_kitsu(query: str) -> dict:
    if not query:
        return {"error": "Query cannot be empty"}
        
    api_url = f"{KITSU_API_URL}?filter[text]={urllib.parse.quote(query)}"
    res_data = query_kitsu_api(api_url)
    if "error" in res_data:
        return res_data
        
    data_list = res_data.get("data", [])
    if not data_list:
        return {"error": f"No results found on Kitsu for query: {query}"}
        
    return extract_kitsu_media_details(data_list[0])
