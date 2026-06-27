import re
import json
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.iafd.com"

def fetch_movie_metadata(movie_id):
    url = f"{BASE_URL}/title.rme/id={movie_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        return {"error": str(e)}

    # Extract title
    title_el = soup.find("title")
    title = title_el.text.strip().replace(" - IAFD", "") if title_el else ""

    # Extract release year
    year_el = soup.find("b", string=re.compile(r"Year"))
    release_date = ""
    if year_el:
        parent = year_el.find_parent("td")
        if parent:
            text = parent.get_text()
            match = re.search(r"(\d{4})", text)
            if match:
                release_date = match.group(1)

    # Extract performers
    performers = []
    performer_links = soup.select("a[href*='person.rme/perfid=']")
    for p in performer_links[:20]:
        name = p.text.strip()
        href = p.get("href", "")
        perf_id = ""
        id_match = re.search(r"perfid=([^&/]+)", href)
        if id_match:
            perf_id = id_match.group(1)
        if name:
            performers.append({
                "name": name,
                "id": perf_id,
                "gender": "f" if "/gender=f" in href else "m"
            })

    # Extract studio
    studio_el = soup.find("a", href=re.compile(r"studio\.rme"))
    studio = studio_el.text.strip() if studio_el else ""

    # Extract director
    director_el = soup.find("a", href=re.compile(r"director\.rme"))
    director = director_el.text.strip() if director_el else ""

    # Image
    portrait = ""
    post_el = soup.find("div", id="headshot")
    if post_el:
        img = post_el.find("img")
        if img:
            portrait = img.get("src", "")

    return {
        "source": "iafd",
        "title": title,
        "url": url,
        "release_date": release_date,
        "performers": performers,
        "studio": studio,
        "director": director,
        "platform": "IAFD",
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

def search_iafd(query):
    url = f"{BASE_URL}/results.rme?search=title&selection={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        return {"error": str(e)}

    # Check if we are already on a title page
    if "/title.rme/id=" in resp.url:
        movie_id_match = re.search(r"id=([^&]+)", resp.url)
        if movie_id_match:
            return fetch_movie_metadata(movie_id_match.group(1))

    # Look for results in a list
    results = []
    for row in soup.select("table#titleresult tr"):
        link = row.find("a", href=re.compile(r"title\.rme/id="))
        if not link:
            continue
        href = link.get("href", "")
        id_match = re.search(r"id=([^&/]+)", href)
        movie_id = id_match.group(1) if id_match else ""
        title = link.text.strip()

        results.append({
            "title": title,
            "id": movie_id,
            "url": f"{BASE_URL}{href}" if href.startswith("/") else f"{BASE_URL}/{href}"
        })

    if results:
        # For our "search" function, we usually return the first result details
        return fetch_movie_metadata(results[0]["id"])

    return {"error": f"No results found on IAFD for query: {query}"}

def iafd(url):
    match = re.search(r"id=([^&/]+)", url)
    if match:
        return fetch_movie_metadata(match.group(1))
    return {"error": "Invalid IAFD URL"}
