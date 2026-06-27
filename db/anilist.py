import re
from curl_cffi import requests

GRAPHQL_URL = "https://graphql.anilist.co"

def extract_anilist_id(url: str) -> int:
    # Match standard patterns like anilist.co/anime/12345/title or anilist.co/anime/12345
    match = re.search(r'anilist\.co/anime/(\d+)', url)
    return int(match.group(1)) if match else None

def query_anilist_api(query_str: str, variables: dict) -> dict:
    try:
        r = requests.post(GRAPHQL_URL, json={"query": query_str, "variables": variables}, timeout=15)
        if r.status_code != 200:
            return {"error": f"AniList GraphQL returned status code {r.status_code}", "details": r.text}
        return r.json()
    except Exception as e:
        return {"error": f"AniList GraphQL request failed: {str(e)}"}

def extract_media_details(media: dict) -> dict:
    if not media:
        return {"error": "No media found in response"}
        
    title_obj = media.get("title", {})
    title = title_obj.get("english") or title_obj.get("romaji") or "Unknown"
    
    start_date = media.get("startDate", {})
    year = start_date.get("year")
    
    display_title = f"{title} - ({year})" if year else title
    
    cover_image = media.get("coverImage", {})
    portrait = cover_image.get("extraLarge") or cover_image.get("large")
    landscape = media.get("bannerImage") or portrait
    
    return {
        "title": display_title,
        "portrait": portrait,
        "landscape": landscape,
        "description": media.get("description", "")
    }

def anilist(url: str) -> dict:
    media_id = extract_anilist_id(url)
    if not media_id:
        return {"error": "Invalid AniList URL, could not extract ID"}
        
    query_str = """
    query ($id: Int) {
      Media (id: $id, type: ANIME) {
        id
        title {
          english
          romaji
        }
        coverImage {
          extraLarge
          large
        }
        bannerImage
        description
        startDate {
          year
        }
      }
    }
    """
    
    res_data = query_anilist_api(query_str, {"id": media_id})
    if "error" in res_data:
        return res_data
        
    media = res_data.get("data", {}).get("Media", {})
    return extract_media_details(media)

def search_anilist(query: str) -> dict:
    if not query:
        return {"error": "Query cannot be empty"}
        
    query_str = """
    query ($search: String) {
      Page (page: 1, perPage: 1) {
        media (search: $search, type: ANIME) {
          id
          title {
            english
            romaji
          }
          coverImage {
            extraLarge
            large
          }
          bannerImage
          description
          startDate {
            year
          }
        }
      }
    }
    """
    
    res_data = query_anilist_api(query_str, {"search": query})
    if "error" in res_data:
        return res_data
        
    media_list = res_data.get("data", {}).get("Page", {}).get("media", [])
    if not media_list:
        return {"error": f"No results found on AniList for query: {query}"}
        
    return extract_media_details(media_list[0])
