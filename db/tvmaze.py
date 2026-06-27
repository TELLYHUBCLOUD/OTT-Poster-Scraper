import re
import urllib.parse
from curl_cffi import requests

TVMAZE_API_URL = "https://api.tvmaze.com"

def extract_tvmaze_id(url: str) -> int:
    # Match standard patterns like tvmaze.com/shows/123/title or tvmaze.com/shows/123
    match = re.search(r'tvmaze\.com/shows/(\d+)', url)
    return int(match.group(1)) if match else None

def query_tvmaze_api(api_url: str) -> dict:
    try:
        r = requests.get(api_url, timeout=15)
        if r.status_code == 404:
            return {"error": "Content not found on TVmaze"}
        if r.status_code != 200:
            return {"error": f"TVmaze API returned status code {r.status_code}"}
        return r.json()
    except Exception as e:
        return {"error": f"TVmaze API request failed: {str(e)}"}

def extract_tvmaze_media_details(data: dict) -> dict:
    if not data:
        return {"error": "No data found"}
        
    title = data.get("name", "Unknown")
    premiered = data.get("premiered", "")
    year = premiered[:4] if premiered else ""
    display_title = f"{title} - ({year})" if year else title
    
    images = data.get("image") or {}
    portrait = images.get("original") or images.get("medium")
    
    # TVmaze does not have a separate background backdrop in this API, fallback to poster
    return {
        "title": display_title,
        "portrait": portrait,
        "landscape": portrait,
        "description": data.get("summary", "")
    }

def tvmaze(url: str) -> dict:
    show_id = extract_tvmaze_id(url)
    if not show_id:
        return {"error": "Invalid TVmaze URL, could not extract ID"}
        
    api_url = f"{TVMAZE_API_URL}/shows/{show_id}"
    res_data = query_tvmaze_api(api_url)
    if "error" in res_data:
        return res_data
        
    return extract_tvmaze_media_details(res_data)

def scrape_tvmaze_episode(show_id: int, season: int, episode: int) -> dict:
    # Get show name first
    show_url = f"{TVMAZE_API_URL}/shows/{show_id}"
    show_data = query_tvmaze_api(show_url)
    show_name = "TV Show"
    show_portrait = None
    if show_data and "error" not in show_data:
        show_name = show_data.get("name", "TV Show")
        show_images = show_data.get("image") or {}
        show_portrait = show_images.get("original") or show_images.get("medium")
        
    ep_url = f"{TVMAZE_API_URL}/shows/{show_id}/episodebynumber?season={season}&number={episode}"
    ep_data = query_tvmaze_api(ep_url)
    if "error" in ep_data:
        return ep_data
        
    ep_name = ep_data.get("name", "Unknown Episode")
    ep_images = ep_data.get("image") or {}
    ep_landscape = ep_images.get("original") or ep_images.get("medium")
    
    display_title = f"{show_name} - S{season:02d}E{episode:02d} - {ep_name}"
    
    return {
        "title": display_title,
        "portrait": show_portrait,
        "landscape": ep_landscape or show_portrait,
        "description": ep_data.get("summary", "")
    }

def search_tvmaze(query: str, season: int = None, episode: int = None) -> dict:
    if not query:
        return {"error": "Query cannot be empty"}
        
    api_url = f"{TVMAZE_API_URL}/singlesearch/shows?q={urllib.parse.quote(query)}"
    res_data = query_tvmaze_api(api_url)
    if "error" in res_data:
        return res_data
        
    show_id = res_data.get("id")
    if season is not None and episode is not None and show_id:
        return scrape_tvmaze_episode(show_id, season, episode)
        
    return extract_tvmaze_media_details(res_data)
