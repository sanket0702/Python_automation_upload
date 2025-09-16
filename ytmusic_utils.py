# ytmusic_utils.py
import json
from ytmusicapi import YTMusic

# Initialize YTMusic only onceimport json
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

ytmusic = YTMusic()


def get_song_by_id(video_id: str) -> dict | None:
    """
    Fetch song metadata from YouTube Music by video ID.
    Returns a dictionary or None if failed.
    """
    try:
        song_data = ytmusic.get_song(video_id)
        return song_data
    except Exception as e:
        print(f"⚠️ Failed to get song: {video_id} → {e}")
        return None


def save_song_to_json(video_id: str, output_file: str) -> None:
    """
    Fetch song metadata and save it to a JSON file.
    """
    song_data = get_song_by_id(video_id)
    if song_data:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(song_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Song metadata saved to {output_file}")
    else:
        print(f"⚠️ No data to save for {video_id}")
