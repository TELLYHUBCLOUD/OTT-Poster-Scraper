import re
import json
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.adultfilmdatabase.com"

def fetch_afd_metadata(movie_id):
    url = f"{BASE_URL}/video.php?id={movie_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        return {"error": str(e)}

    # Title
    title_el = soup.find("h1")
    title = title_el.text.strip() if title_el else ""

    # Release Date
    release_date = ""
    date_el = soup.find("span", string=re.compile(r"Release Date"))
    if date_el:
        parent = date_el.find_parent("li")
        if parent:
            release_date = parent.text.replace("Release Date:", "").strip()

    # Performers
    performers = []
    perf_section = soup.find("div", class_="cast")
    if perf_section:
        for a in perf_section.find_all("a", href=True):
            if "actor.php" in a['href']:
                name = a.text.strip()
                match = re.search(r"id=(\d+)", a['href'])
                perf_id = match.group(1) if match else ""
                performers.append({"name": name, "id": perf_id})

    # Studio
    studio = ""
    studio_el = soup.find("a", href=re.compile(r"studio\.php"))
    if studio_el:
        studio = studio_el.text.strip()

    # Director
    director = ""
    director_el = soup.find("a", href=re.compile(r"director\.php"))
    if director_el:
        director = director_el.text.strip()

    # Images
    portrait = ""
    img_el = soup.find("img", class_="img-responsive")
    if img_el:
        portrait = img_el.get("src", "")
        if portrait and not portrait.startswith("http"):
            portrait = f"{BASE_URL}{portrait}"

    return {
        "source": "afd",
        "title": title,
        "url": url,
        "release_date": release_date,
        "performers": performers,
        "studio": studio,
        "director": director,
        "platform": "Adult Film Database",
        "images": {
            "landscape": "",
            "portrait": portrait,
            "banner": ""
        },
        "metadata": {
            "description": "",
            "tags": [],
            "duration_min": 0,
            "rating": 0.0
        }
    }

def search_afd(query):
    url = f"{BASE_URL}/lookup.php?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        return {"error": str(e)}

    # Results
    link = soup.find("a", href=re.compile(r"video\.php\?id="))
    if link:
        match = re.search(r"id=(\d+)", link['href'])
        if match:
            return fetch_afd_metadata(match.group(1))

    return {"error": f"No results found on AFD for query: {query}"}

def afd(url):
    match = re.search(r"id=(\d+)", url)
    if match:
        return fetch_afd_metadata(match.group(1))
    return {"error": "Invalid AFD URL"}
