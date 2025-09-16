import json
import os
from ytmusicapi import YTMusic
import sys
import io
from datetime import datetime

# Fix stdout for unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def fetch_playlist_full_metadata(playlist_id):
    ytmusic = YTMusic()
    
    try:
        playlist = ytmusic.get_playlist(playlist_id, limit=100)
    except Exception as e:
        print("[ERROR] Failed to fetch playlist:", e, file=sys.stderr)
        return

    all_songs_data = []

    for idx, track in enumerate(playlist["tracks"], start=1):
        
        videoId = track.get("videoId")
        if idx>1:
            break
        if not videoId:
            continue

        try:
            # Fetch full metadata for each song
            metadata = ytmusic.get_song(videoId)
        except Exception as e:
            print(f"[ERROR] Failed to fetch metadata for {videoId}: {e}", file=sys.stderr)
            continue

        thumbnails = metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("thumbnail", {}).get("thumbnails", [])
        coverUrl = thumbnails[0]["url"] if thumbnails else None

        pub_date_str = metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("publishDate")
        

        # Extract essential fields
        song_data = {
           "videoId": videoId,
            "title": metadata.get("videoDetails", {}).get("title"),
            "artist": metadata.get("videoDetails", {}).get("author"),
            "coverUrl": coverUrl,
            "description": metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("tags"),
            "urlCanonical": metadata.get("videoDetails", {}).get("video_url"),
            "viewCount": metadata.get("videoDetails", {}).get("viewCount"),
            "publishDate": pub_date_str,
            "category": metadata.get("videoDetails", {}).get("category"),
            "tags": metadata.get("microformat", {}).get("microformatDataRenderer", {}).get("tags"),

            #"streamingData": metadata.get("streamingData"),
            #"playabilityStatus": metadata.get("playabilityStatus"),
            "videoDetails": metadata.get("videoDetails"),
            #"microformat": metadata.get("microformat"),
            #"siteName": "YouTube Music",
            #"appName": "YouTube Music",
            #"androidPackage": "com.google.android.apps.youtube.music",
            #"iosAppStoreId": "1017492454",
            #"urls": {
                #"iosAppArguments": f"https://music.youtube.com/watch?v={videoId}",
                #"urlApplinksIos": f"vnd.youtube.music://music.youtube.com/watch?v={videoId}&feature=applinks",
                #"urlApplinksAndroid": f"vnd.youtube.music://music.youtube.com/watch?v={videoId}&feature=applinks",
                #"urlTwitterIos": f"vnd.youtube.music://music.youtube.com/watch?v={videoId}&feature=twitter-deep-link",
                #"urlTwitterAndroid": f"vnd.youtube.music://music.youtube.com/watch?v={videoId}&feature=twitter-deep-link",
           # }
        }

        all_songs_data.append(song_data)
        print(f"[{idx}] {song_data['title']} - {song_data['urlCanonical']}", file=sys.stderr)

    # Save all songs in JSON
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/playlist_full_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_songs_data, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved full playlist metadata to {filename}", file=sys.stderr)

if __name__ == "__main__":
    playlist_id = "PL4fGSI1pDJn40WjZ6utkIuj2rNg-7iGsq"
    fetch_playlist_full_metadata(playlist_id)
