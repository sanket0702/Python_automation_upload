import json
from ytmusicapi import YTMusic

ytmusic = YTMusic()

def get_song_by_id(video_id: str) -> dict | None:
    """Fetch song metadata from YouTube Music by video ID."""
    try:
        metadata = ytmusic.get_song(video_id)
        thumbnails = metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("thumbnail", {}).get("thumbnails", [])
        coverUrl = thumbnails[0]["url"] if thumbnails else None
        pub_date_str = metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("publishDate")

        details = {
            "videoId": metadata.get("videoDetails", {}).get("videoId"),
            "title": metadata.get("videoDetails", {}).get("title"),
            "artist": metadata.get("videoDetails", {}).get("author"),
            "coverUrl": coverUrl,
            "description": metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("description"),
            "urlCanonical": metadata.get("videoDetails", {}).get("video_url"),
            "viewCount": metadata.get("videoDetails", {}).get("viewCount"),
            "publishDate": pub_date_str,
            "category": metadata.get("videoDetails", {}).get("category"),
            "tags": metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("tags"),
        }
        return details
    except Exception as e:
        print(f"⚠️ Failed to get song: {video_id} → {e}")
        return None
