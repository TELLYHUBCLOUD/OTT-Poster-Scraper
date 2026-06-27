import re
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

def extract_mdl_slug_and_id(url: str) -> tuple:
    # Match standard patterns like mydramalist.com/12345-slug or mydramalist.com/12345
    # Remove query/fragment
    url_clean = url.split("?")[0].split("#")[0].strip("/")
    match = re.search(r'mydramalist\.com/(\d+)-([a-zA-Z0-9-]+)', url_clean)
    if match:
        return match.group(1), match.group(2)
        
    # Match just ID in URL
    match_id = re.search(r'mydramalist\.com/(\d+)/?$', url_clean)
    if match_id:
        return match_id.group(1), None
        
    return None, None

def scrape_mdl_details(drama_id: str, slug: str = None) -> dict:
    url = f"https://mydramalist.com/{drama_id}"
    if slug:
        url = f"https://mydramalist.com/{drama_id}-{slug}"
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://mydramalist.com/"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"MyDramaList details page returned status code {r.status_code}"}
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Title
        title_meta = soup.find("meta", property="og:title")
        title = title_meta["content"] if title_meta else "Unknown"
        
        # Poster
        img_meta = soup.find("meta", property="og:image")
        poster = img_meta["content"] if img_meta else None
        if poster and poster.startswith("//"):
            poster = "https:" + poster
            
        # Description
        desc_meta = soup.find("meta", property="og:description")
        description = desc_meta["content"] if desc_meta else ""
        
        return {
            "title": title,
            "portrait": poster,
            "landscape": poster, # MDL usually doesn't have landscape backdrops in og tags
            "description": description
        }
    except Exception as e:
        return {"error": f"Failed web scraping MyDramaList details: {str(e)}"}

def mydramalist(url: str) -> dict:
    drama_id, slug = extract_mdl_slug_and_id(url)
    if not drama_id:
        return {"error": "Invalid MyDramaList URL, could not extract ID"}
        
    return scrape_mdl_details(drama_id, slug)

def search_mydramalist(query: str) -> dict:
    url = f"https://mydramalist.com/search?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://mydramalist.com/"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"MyDramaList search returned status code {r.status_code}"}
            
        # Find first matching drama slug like "/12345-slug"
        links = re.findall(r'href=["\']/(\d+)-([a-zA-Z0-9-]+)["\']', r.text)
        if not links:
            return {"error": f"No results found on MyDramaList for query: {query}"}
            
        drama_id, slug = links[0]
        return scrape_mdl_details(drama_id, slug)
    except Exception as e:
        return {"error": f"Failed searching MyDramaList: {str(e)}"}
