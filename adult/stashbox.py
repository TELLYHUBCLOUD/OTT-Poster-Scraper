import os
import json
from curl_cffi import requests

# Default StashDB
API_ENDPOINT = "https://stashdb.org/graphql"
STASH_API_KEY = os.getenv("STASH_API_KEY", "")

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}
if STASH_API_KEY:
    HEADERS["ApiKey"] = STASH_API_KEY # Stashbox often uses ApiKey header

SEARCH_SCENES_QUERY = """
query SearchScenes($term: String!) {
  searchScene(term: $term) {
    scenes {
      id
      title
      details
      release_date
      duration
      director
      studio {
        name
      }
      performers {
        performer {
          id
          name
          image_url
        }
      }
      images {
        url
        type
      }
    }
  }
}
"""

def _convert(s):
    performers = []
    for p in s.get("performers", []):
        perf = p.get("performer", {})
        performers.append({
            "name": perf.get("name", ""),
            "id": perf.get("id", ""),
            "image_url": perf.get("image_url", ""),
        })

    landscape_url = ""
    portrait_url = ""
    banner_url = ""
    for img in s.get("images", []):
        url = img.get("url", "")
        t = img.get("type", "").lower()
        if "landscape" in t or "background" in t:
            landscape_url = url
        elif "portrait" in t or "poster" in t:
            portrait_url = url
        elif "banner" in t:
            banner_url = url
        if not landscape_url and not portrait_url:
            portrait_url = url

    return {
        "source": "stash-box",
        "id": s.get("id", ""),
        "title": s.get("title", ""),
        "url": "", # Stashbox is decentralized, no single scene URL
        "release_date": s.get("release_date", ""),
        "performers": performers,
        "studio": s.get("studio", {}).get("name", "") if s.get("studio") else "",
        "director": s.get("director", ""),
        "platform": "Stash-box",
        "images": {
            "landscape": landscape_url,
            "portrait": portrait_url,
            "banner": banner_url
        },
        "metadata": {
            "description": s.get("details", ""),
            "duration_sec": s.get("duration", 0),
        }
    }

def search_stashbox(query):
    payload = {"query": SEARCH_SCENES_QUERY, "variables": {"term": query}}
    try:
        resp = requests.post(API_ENDPOINT, json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": str(e)}

    scenes = data.get("data", {}).get("searchScene", {}).get("scenes", [])
    if not scenes:
        return {"error": f"No results found on Stash-box for: {query}"}

    return _convert(scenes[0])

def stashbox(url):
    # If URL is a specific Stash-box ID or similar
    import re
    match = re.search(r'scenes/([a-f0-9-]+)', url)
    if match:
        scene_id = match.group(1)
        FIND_QUERY = """
        query FindScene($id: ID!) {
          findScene(id: $id) {
            id
            title
            details
            release_date
            duration
            director
            studio { name }
            performers { performer { name id image_url } }
            images { url type }
          }
        }
        """
        payload = {"query": FIND_QUERY, "variables": {"id": scene_id}}
        try:
            resp = requests.post(API_ENDPOINT, json=payload, headers=HEADERS, timeout=15)
            data = resp.json()
            scene = data.get("data", {}).get("findScene")
            if scene:
                return _convert(scene)
        except Exception:
            pass
    return {"error": "Invalid Stash-box URL or scene not found"}
