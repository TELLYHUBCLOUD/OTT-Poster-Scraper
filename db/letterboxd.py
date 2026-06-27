import re
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

def extract_letterboxd_slug(url: str) -> str:
    # Match standard patterns like letterboxd.com/film/slug
    # Remove query/fragment
    url_clean = url.split("?")[0].split("#")[0].strip("/")
    match = re.search(r'letterboxd\.com/film/([a-zA-Z0-9-]+)', url_clean)
    return match.group(1) if match else None

def scrape_letterboxd_details(slug: str) -> dict:
    url = f"https://letterboxd.com/film/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://letterboxd.com/"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"Letterboxd details page returned status code {r.status_code}"}
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Title
        title_meta = soup.find("meta", property="og:title")
        title = title_meta["content"] if title_meta else "Unknown"
        
        # Clean title suffix " • Film"
        title = re.sub(r'\s*•\s*Film', '', title, flags=re.I).strip()
        
        # Poster
        img_meta = soup.find("meta", property="og:image")
        poster = img_meta["content"] if img_meta else None
        
        # In Letterboxd, the og:image is often the poster but cropped.
        # But we can find the full poster inside the page HTML:
        # e.g. look for an img tag with class "image" inside div with class "poster"
        # Or look for JSON-LD which Letterboxd often includes!
        script = soup.find("script", type="application/ld+json")
        description = ""
        if script:
            try:
                # Sometimes Letterboxd puts multiple JSON-LD, or wraps in CDATA
                text = script.string
                # clean comments
                text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
                data = json.loads(text)
                if isinstance(data, dict):
                    description = data.get("description", "")
            except Exception:
                pass
                
        # If og:image has a size limit in query, let's keep it clean
        if poster:
            # e.g. https://a.ltrbxd.com/resized/film-poster/...-0-1000-0-1500-crop.jpg
            # Letterboxd resizing allows getting the original poster:
            # We can strip the resize elements if needed, but og:image usually is high res enough.
            pass
            
        return {
            "title": title,
            "portrait": poster,
            "landscape": poster,
            "description": description
        }
    except Exception as e:
        return {"error": f"Failed web scraping Letterboxd details: {str(e)}"}

def letterboxd(url: str) -> dict:
    slug = extract_letterboxd_slug(url)
    if not slug:
        return {"error": "Invalid Letterboxd URL, could not extract film slug"}
        
    return scrape_letterboxd_details(slug)

def search_letterboxd(query: str) -> dict:
    url = f"https://letterboxd.com/search/films/{urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://letterboxd.com/"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"Letterboxd search returned status code {r.status_code}"}
            
        # Find first matching film link: e.g. "/film/fight-club/"
        links = re.findall(r'href=["\']/film/([a-zA-Z0-9-]+)/?["\']', r.text)
        if not links:
            return {"error": f"No results found on Letterboxd for query: {query}"}
            
        slug = links[0]
        return scrape_letterboxd_details(slug)
    except Exception as e:
        return {"error": f"Failed searching Letterboxd: {str(e)}"}
