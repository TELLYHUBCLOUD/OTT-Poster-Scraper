import re
import json
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

def extract_imdb_id(url: str) -> str:
    match = re.search(r'(tt\d+)', url)
    return match.group(1) if match else None

def fetch_imdb_suggestion_api(imdb_id: str) -> dict:
    first_char = imdb_id[0].lower() if imdb_id else "t"
    url = f"https://v3.sg.media-imdb.com/suggestion/{first_char}/{imdb_id}.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = data.get("d", [])
            if results:
                top = results[0]
                title = top.get("l", "Unknown")
                year = top.get("y")
                display_title = f"{title} - ({year})" if year else title
                img_data = top.get("i")
                poster = img_data.get("imageUrl") if isinstance(img_data, dict) else None
                return {
                    "title": display_title,
                    "portrait": poster,
                    "landscape": poster,
                    "description": top.get("s", "")
                }
    except Exception:
        pass
    return None

def scrape_imdb(imdb_id: str) -> dict:
    url = f"https://www.imdb.com/title/{imdb_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            fallback_res = fetch_imdb_suggestion_api(imdb_id)
            if fallback_res:
                return fallback_res
            return {"error": f"IMDb returned status code {r.status_code}"}
            
        soup = BeautifulSoup(r.text, "html.parser")
        script = soup.find("script", type="application/ld+json")
        
        if not script:
            # Fallback to meta tags
            title_meta = soup.find("meta", property="og:title")
            img_meta = soup.find("meta", property="og:image")
            
            title = title_meta["content"] if title_meta else "Unknown"
            poster = img_meta["content"] if img_meta else None
            return {
                "title": title,
                "portrait": poster,
                "landscape": poster
            }
            
        data = json.loads(script.string)
        title = data.get("name", "Unknown")
        date_published = data.get("datePublished", "")
        year = date_published[:4] if date_published else ""
        
        display_title = f"{title} - ({year})" if year else title
        poster = data.get("image")
        
        # Get background/backdrop from og:image or page metadata
        og_img_meta = soup.find("meta", property="og:image")
        backdrop = og_img_meta["content"] if og_img_meta else poster
        
        return {
            "title": display_title,
            "portrait": poster,
            "landscape": backdrop,
            "description": data.get("description", ""),
            "rating": data.get("aggregateRating", {}).get("ratingValue")
        }
    except Exception as e:
        fallback_res = fetch_imdb_suggestion_api(imdb_id)
        if fallback_res:
            return fallback_res
        return {"error": f"Failed to scrape IMDb: {str(e)}"}

def get_episode_imdb_id(series_id: str, season: int, episode: int) -> str:
    url = f"https://www.imdb.com/title/{series_id}/episodes/?season={season}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return None
            
        # Match class or attributes containing the episode number and the tt ID
        # In modern IMDb episode lists, each episode block has class containing e.g. "ipc-metadata-list-summary-item"
        # and links containing /title/tt12345/
        # Or we can look for specific links containing tt numbers and names
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Search for all links with /title/tt... and look for the one matching the episode index
        # Let's inspect links
        ep_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Look for /title/tt\d+/
            match = re.search(r'/title/(tt\d+)/?', href)
            if match:
                tt_id = match.group(1)
                # Avoid duplicate matching and match main titles
                if tt_id != series_id and tt_id not in ep_links:
                    ep_links.append(tt_id)
        
        # In IMDb, the list of episode IDs for the season is usually ordered: Episode 1, Episode 2, etc.
        # If we want Episode 2, index is 1 (episode - 1)
        if ep_links and len(ep_links) >= episode:
            # Let's double check if there are duplicate links (e.g. image link and text link)
            # We can pick the one at (episode - 1)
            # To be absolutely sure, let's find the card element for this episode
            # E.g. search for text "S1, Ep2" or similar
            # If we can't find direct text, index selection is a great fallback!
            return ep_links[episode - 1]
            
    except Exception:
        pass
    return None

def search_imdb(query: str, season: int = None, episode: int = None) -> dict:
    if not query:
        return {"error": "Query cannot be empty"}
        
    first_char = query[0].lower() if query else "a"
    if not first_char.isalnum():
        first_char = "a"
        
    url = f"https://v3.sg.media-imdb.com/suggestion/{first_char}/{urllib.parse.quote(query.lower())}.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"IMDb suggestion API returned {r.status_code}"}
            
        data = r.json()
        results = data.get("d", [])
        if not results:
            return {"error": f"No results found on IMDb for query: {query}"}
            
        # Extract first result with a valid tt ID
        top_result = None
        for res in results:
            res_id = res.get("id", "")
            if res_id.startswith("tt"):
                top_result = res
                break
                
        if not top_result:
            return {"error": f"No valid movies or series found on IMDb for query: {query}"}
            
        imdb_id = top_result.get("id")
        
        if season is not None and episode is not None:
            # It's an episode query
            ep_id = get_episode_imdb_id(imdb_id, season, episode)
            if ep_id:
                res = scrape_imdb(ep_id)
                if "error" not in res:
                    return res
                # If episode scraping failed, fall back to series scraping
                
        # Return the top result metadata directly from the search result!
        title = top_result.get("l", "Unknown")
        year = top_result.get("y")
        display_title = f"{title} - ({year})" if year else title
        img_data = top_result.get("i")
        poster = img_data.get("imageUrl") if isinstance(img_data, dict) else None
        
        return {
            "title": display_title,
            "portrait": poster,
            "landscape": poster,
            "description": top_result.get("s", "")
        }
        
    except Exception as e:
        return {"error": f"Failed searching IMDb: {str(e)}"}

def imdb(url: str) -> dict:
    imdb_id = extract_imdb_id(url)
    if not imdb_id:
        return {"error": "Invalid IMDb URL, could not extract ID"}
    return scrape_imdb(imdb_id)
