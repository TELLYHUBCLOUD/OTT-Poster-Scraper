import json
from curl_cffi import requests

API_BASE = "https://prdb.net/api"

def lookup_by_hash(oshash=None, phash=None):
    params = {}
    if oshash:
        params["oshash"] = oshash
    if phash:
        params["phash"] = phash

    try:
        resp = requests.get(f"{API_BASE}/v1/lookup", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": str(e)}

    if not data.get("matched"):
        return {"error": "No match found"}

    scene = data.get("scene", {})
    return _convert_scene(scene)

def _convert_scene(scene):
    actors_raw = scene.get("actors", [])
    performers = []
    if isinstance(actors_raw, list):
        for a in actors_raw:
            if isinstance(a, dict):
                performers.append({"name": a.get("name", ""), "id": a.get("id", "")})
            else:
                performers.append({"name": str(a), "id": ""})

    previews = scene.get("previews", [])
    spritesheet = scene.get("spritesheet", "")

    return {
        "source": "prdb",
        "id": scene.get("id", ""),
        "title": scene.get("title", ""),
        "url": f"https://prdb.net/scenes/{scene.get('id', '')}" if scene.get('id') else "",
        "release_date": scene.get("released", ""),
        "performers": performers,
        "studio": scene.get("site", ""),
        "director": "",
        "platform": "PRDB",
        "images": {
            "landscape": previews[0] if previews else "",
            "portrait": "",
            "banner": spritesheet
        },
        "metadata": {
            "description": scene.get("description", ""),
            "tags": scene.get("tags", []),
            "duration_sec": scene.get("duration", 0),
        }
    }

def search_prdb(query):
    # PRDB API doesn't seem to have a public search by title endpoint in the snippet provided
    # but I can try to find if there is one.
    # For now, I'll mark it as unsupported or use lookup if query looks like hash.
    if len(query) == 16 and all(c in '0123456789abcdefABCDEF' for c in query):
        return lookup_by_hash(oshash=query)
    return {"error": "PRDB only supports hash-based lookup in this implementation"}

def prdb(url):
    import re
    match = re.search(r'scenes/(\d+)', url)
    if match:
        scene_id = match.group(1)
        # We might need a specific get endpoint for PRDB
        try:
            resp = requests.get(f"{API_BASE}/v1/scene/{scene_id}", timeout=15)
            if resp.status_code == 200:
                return _convert_scene(resp.json())
        except Exception:
            pass
    return {"error": "Invalid PRDB URL"}
