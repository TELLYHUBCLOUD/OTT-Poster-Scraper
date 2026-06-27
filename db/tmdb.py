import os
import re
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_IMAGE_URL = "https://image.tmdb.org/t/p"

def extract_tmdb_id_and_type(url: str):
    # Match standard patterns like themoviedb.org/movie/123 or themoviedb.org/tv/456
    match = re.search(r'themoviedb\.org/(movie|tv)/(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def scrape_tmdb_details_api(content_type: str, content_id: str, season: int = None, episode: int = None) -> dict:
    headers = {"Accept": "application/json"}
    
    # If episode details are requested
    if content_type == "tv" and season is not None and episode is not None:
        url = f"https://api.themoviedb.org/3/tv/{content_id}/season/{season}/episode/{episode}?api_key={TMDB_API_KEY}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                title = data.get("name", "Unknown Episode")
                still_path = data.get("still_path")
                landscape = f"{BASE_IMAGE_URL}/original{still_path}" if still_path else None
                
                # For portrait fallback, fetch series details to get series poster
                series_url = f"https://api.themoviedb.org/3/tv/{content_id}?api_key={TMDB_API_KEY}"
                r_series = requests.get(series_url, headers=headers, timeout=15)
                portrait = None
                series_name = "Unknown Show"
                if r_series.status_code == 200:
                    s_data = r_series.json()
                    series_name = s_data.get("name", "Unknown Show")
                    post_path = s_data.get("poster_path")
                    portrait = f"{BASE_IMAGE_URL}/w500{post_path}" if post_path else None
                    
                display_title = f"{series_name} - S{season:02d}E{episode:02d} - {title}"
                
                return {
                    "title": display_title,
                    "portrait": portrait,
                    "landscape": landscape,
                    "description": data.get("overview", "")
                }
        except Exception:
            pass

    # Standard movie/tv details API
    url = f"https://api.themoviedb.org/3/{content_type}/{content_id}?api_key={TMDB_API_KEY}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return {"error": f"TMDB API returned status code {r.status_code}"}
            
        data = r.json()
        title = data.get("title") or data.get("name") or "Unknown"
        year = ""
        date_str = data.get("release_date") or data.get("first_air_date")
        if date_str:
            year = date_str[:4]
            
        display_title = f"{title} - ({year})" if year else title
        
        poster_path = data.get("poster_path")
        backdrop_path = data.get("backdrop_path")
        
        portrait = f"{BASE_IMAGE_URL}/w500{poster_path}" if poster_path else None
        landscape = f"{BASE_IMAGE_URL}/original{backdrop_path}" if backdrop_path else portrait
        
        return {
            "title": display_title,
            "portrait": portrait,
            "landscape": landscape,
            "description": data.get("overview", "")
        }
    except Exception as e:
        return {"error": f"TMDB API request failed: {str(e)}"}

def scrape_tmdb_details_web(content_type: str, content_id: str, season: int = None, episode: int = None) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.themoviedb.org/"
    }
    
    # TV Episode Scraper fallback
    if content_type == "tv" and season is not None and episode is not None:
        url = f"https://www.themoviedb.org/tv/{content_id}/season/{season}/episode/{episode}"
        try:
            r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Extract show title and episode title
                # Title format: "Game of Thrones: Season 1 (2011) - Episode 2..."
                title_tag = soup.find("title")
                full_title = title_tag.text.strip() if title_tag else ""
                show_title = full_title.split(":")[0].strip() if ":" in full_title else "TV Show"
                
                # Find the episode title in the page
                # We can search for the active episode's title link or details
                # Usually it has data-episode-number="{episode}"
                ep_link = soup.find(lambda tag: tag.name == "a" and tag.get("data-episode-number") == str(episode))
                ep_title = ep_link.text.strip() if ep_link else f"Episode {episode}"
                
                # Landscape (still image)
                # Find image containing alt=ep_title or class contains backdrop
                img_tag = soup.find("img", alt=ep_title)
                landscape_url = None
                if img_tag:
                    src = img_tag.get("src") or img_tag.get("data-src")
                    if src:
                        # Convert to original resolution
                        # e.g. /t/p/w160_and_h90_face/... -> /t/p/original/...
                        src_path = re.sub(r'/t/p/[^/]+', '/t/p/original', src)
                        if src_path.startswith("//"):
                            landscape_url = "https:" + src_path
                        elif src_path.startswith("/"):
                            landscape_url = "https://media.themoviedb.org" + src_path
                        else:
                            landscape_url = src_path
                
                # Portrait: Fallback to series main poster
                portrait_url = None
                series_link = soup.find("a", href=True) # Let's fetch the main TV show page
                if series_link:
                    # Fetch show details web page to get poster
                    s_url = f"https://www.themoviedb.org/tv/{content_id}"
                    r_series = requests.get(s_url, headers=headers, impersonate="chrome", timeout=15)
                    if r_series.status_code == 200:
                        s_soup = BeautifulSoup(r_series.text, "html.parser")
                        post_meta = s_soup.find("meta", property="og:image")
                        if post_meta:
                            portrait_url = post_meta["content"]
                            
                display_title = f"{show_title} - S{season:02d}E{episode:02d} - {ep_title}"
                return {
                    "title": display_title,
                    "portrait": portrait_url,
                    "landscape": landscape_url or portrait_url
                }
        except Exception:
            pass

    # Standard movie/tv details page scraper
    url = f"https://www.themoviedb.org/{content_type}/{content_id}"
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return {"error": f"TMDB details scraping returned status code {r.status_code}"}
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Title
        title_meta = soup.find("meta", property="og:title")
        title = title_meta["content"] if title_meta else "Unknown"
        
        # Year
        year_match = re.search(r'\((\d{4})\)', title)
        year = year_match.group(1) if year_match else ""
        
        # Clean title (remove year suffix if present in meta)
        clean_title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
        display_title = f"{clean_title} - ({year})" if year else clean_title
        
        # Portrait (og:image)
        post_meta = soup.find("meta", property="og:image")
        portrait = post_meta["content"] if post_meta else None
        if portrait and portrait.startswith("//"):
            portrait = "https:" + portrait
            
        # Backdrop
        # Look for the background image path /t/p/original/ or multi_faces
        html_text = r.text
        backdrop_match = re.search(r'/(t/p/(?:w1920_and_h800_multi_faces|w533_and_h300_face|w1066_and_h600_face|original)/[a-zA-Z0-9_-]+\.(?:jpg|png|jpeg))', html_text)
        
        landscape = portrait
        if backdrop_match:
            landscape = "https://media.themoviedb.org/" + backdrop_match.group(1)
            
        return {
            "title": display_title,
            "portrait": portrait,
            "landscape": landscape
        }
    except Exception as e:
        return {"error": f"Failed web scraping TMDB details: {str(e)}"}

def tmdb(url: str, season: int = None, episode: int = None) -> dict:
    c_type, c_id = extract_tmdb_id_and_type(url)
    if not c_type or not c_id:
        return {"error": "Invalid TMDB URL, could not extract type and ID"}
        
    if TMDB_API_KEY:
        return scrape_tmdb_details_api(c_type, c_id, season, episode)
    else:
        return scrape_tmdb_details_web(c_type, c_id, season, episode)

def search_tmdb_web(query: str) -> tuple:
    url = f"https://www.themoviedb.org/search?query={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.themoviedb.org/"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return None, None
            
        # Match movie/tv links
        links = re.findall(r'href=["\']/(movie|tv)/(\d+)[^"\']*["\']', r.text)
        if links:
            return links[0] # Return (type, id) of the first result
    except Exception:
        pass
    return None, None

def search_tmdb_api(query: str) -> tuple:
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={urllib.parse.quote(query)}"
    headers = {"Accept": "application/json"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            for res in results:
                m_type = res.get("media_type")
                if m_type in ["movie", "tv"]:
                    return m_type, str(res.get("id"))
    except Exception:
        pass
    return None, None

def search_tmdb(query: str, season: int = None, episode: int = None) -> dict:
    if TMDB_API_KEY:
        c_type, c_id = search_tmdb_api(query)
    else:
        c_type, c_id = search_tmdb_web(query)
        
    if not c_type or not c_id:
        return {"error": f"No movie or series found on TMDB for query: {query}"}
        
    if TMDB_API_KEY:
        return scrape_tmdb_details_api(c_type, c_id, season, episode)
    else:
        return scrape_tmdb_details_web(c_type, c_id, season, episode)
