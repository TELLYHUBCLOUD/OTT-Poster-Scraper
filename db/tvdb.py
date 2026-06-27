import re
from curl_cffi import requests
from bs4 import BeautifulSoup

def extract_tvdb_slug(url: str) -> tuple:
    # Match standard patterns like thetvdb.com/series/slug or thetvdb.com/movies/slug
    match = re.search(r'thetvdb\.com/(series|movies)/([a-zA-Z0-9-]+)', url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def scrape_tvdb(content_type: str, slug: str) -> dict:
    url = f"https://thetvdb.com/{content_type}/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://thetvdb.com/"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"TVDB details page returned status code {r.status_code}"}
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Title
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "Unknown"
        # Clean title suffix "- TheTVDB.com"
        title = re.sub(r'\s*-\s*TheTVDB\.com', '', title, flags=re.I).strip()
        
        # Search the HTML for artworks banner urls
        html_text = r.text
        
        # Poster image (containing /posters/)
        poster_match = re.search(r'(https://artworks\.thetvdb\.com/banners/(?:v4/series/\d+/posters|posters|series/\d+/posters)/[a-zA-Z0-9_-]+\.(?:jpg|png|jpeg))', html_text)
        
        # Backdrop image (containing /backgrounds/ or /fanart/original/)
        backdrop_match = re.search(r'(https://artworks\.thetvdb\.com/banners/(?:v4/series/\d+/backgrounds|fanart/original)/[a-zA-Z0-9_-]+\.(?:jpg|png|jpeg))', html_text)
        
        poster = poster_match.group(1) if poster_match else None
        backdrop = backdrop_match.group(1) if backdrop_match else poster
        
        return {
            "title": title,
            "portrait": poster,
            "landscape": backdrop
        }
    except Exception as e:
        return {"error": f"Failed web scraping TVDB details: {str(e)}"}

def tvdb(url: str) -> dict:
    content_type, slug = extract_tvdb_slug(url)
    if not content_type or not slug:
        return {"error": "Invalid TVDB URL, could not extract type and slug"}
        
    return scrape_tvdb(content_type, slug)
