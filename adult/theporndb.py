import os
import json
from curl_cffi import requests

API_ENDPOINT = "https://theporndb.net/graphql"
TPDB_API_KEY = os.getenv("TPDB_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {TPDB_API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

SEARCH_SCENE_QUERY = """
query SearchScene($term: String!) {
  searchScene(term: $term) {
    scenes {
      id
      title
      details
      release_date
      duration
      director
      code
      studio {
        id
        name
        url
      }
      performers {
        performer {
          id
          name
          birth_date
          gender
          image_url
          aliases
        }
      }
      tags {
        id
        name
      }
      images {
        id
        url
        width
        height
        type
      }
      urls {
        url
        type
      }
    }
  }
}
"""

def graphql_request(query, variables):
    payload = {
        "query": query,
        "variables": variables
    }
    try:
        resp = requests.post(API_ENDPOINT, json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"errors": [{"message": str(e)}]}

def _convert_scene(s):
    performers = [
        {
            "name": p.get("performer", {}).get("name", ""),
            "id": p.get("performer", {}).get("id", ""),
            "gender": p.get("performer", {}).get("gender", ""),
            "image_url": p.get("performer", {}).get("image_url", ""),
        }
        for p in s.get("performers", [])
    ]

    landscape_url = ""
    portrait_url = ""
    banner_url = ""

    for img in s.get("images", []):
        img_type = img.get("type", "")
        url = img.get("url", "")
        if "landscape" in img_type.lower() or "background" in img_type.lower():
            landscape_url = url
        elif "portrait" in img_type.lower() or "poster" in img_type.lower():
            portrait_url = url
        elif "banner" in img_type.lower():
            banner_url = url

    tags = [t.get("name", "") for t in s.get("tags", [])]

    return {
        "source": "theporndb",
        "id": s.get("id", ""),
        "title": s.get("title", ""),
        "url": f"https://theporndb.net/scenes/{s.get('id', '')}" if s.get('id') else "",
        "release_date": s.get("release_date", ""),
        "performers": performers,
        "studio": s.get("studio", {}).get("name", "") if s.get("studio") else "",
        "director": s.get("director", ""),
        "platform": "ThePornDB",
        "images": {
            "landscape": landscape_url,
            "portrait": portrait_url,
            "banner": banner_url
        },
        "metadata": {
            "description": s.get("details", ""),
            "tags": tags,
            "duration_sec": s.get("duration", 0),
        }
    }

def search_theporndb(query):
    if not TPDB_API_KEY:
        return {"error": "TPDB_API_KEY not set"}
    result = graphql_request(SEARCH_SCENE_QUERY, {"term": query})
    if "errors" in result:
        return {"error": result["errors"]}

    scenes = result.get("data", {}).get("searchScene", {}).get("scenes", [])
    if not scenes:
        return {"error": f"No results found on ThePornDB for: {query}"}

    return _convert_scene(scenes[0])

def theporndb(url):
    # Extract ID from URL if possible, otherwise search by title or something?
    # Usually URLs are like https://theporndb.net/scenes/uuid
    import re
    match = re.search(r'scenes/([a-f0-9-]+)', url)
    if match:
        scene_id = match.group(1)
        # We need a findScene query
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
            tags { name }
            images { url type }
          }
        }
        """
        result = graphql_request(FIND_QUERY, {"id": scene_id})
        if "errors" in result:
            return {"error": result["errors"]}
        scene = result.get("data", {}).get("findScene")
        if scene:
            return _convert_scene(scene)
    return {"error": "Invalid ThePornDB URL or scene not found"}
