import os
import json
from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError, TKEY, COMM
import sys
import io
from ytmusic_utils import get_song_by_id

# Ensure stdout/stderr handles UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "Download_Songs"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def sanitize_filename(name):
    """Remove invalid filesystem characters."""
    if not name:
        name = "Unknown"
    return "".join(c for c in name if c.isalnum() or c in " ._-").rstrip()


def download_mp3(song, album=None):
    # Construct URL
    url = song.get("urlCanonical") or (
        f"https://music.youtube.com/watch?v={song.get('videoId')}" if song.get("videoId") else None
    )
    if not url:
        print(f"[SKIP] No valid URL for: {song.get('title', 'Unknown')}")
        return

    # Extract basic info
    title = song.get("title") or "Unknown Title"
    artist = song.get("artist") or "Unknown Artist"
    tags = song.get("tags") or []
    publishdate = song.get("publishDate")
    video_id = song.get("videoId")
    coverUrl = song.get("coverUrl", "")
    
    print(f"✅ Starting download: {title} | Artist: {artist} | VideoID: {video_id}")

    # yt-dlp options
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        "cookiefile": "cookies.txt",  # must be Netscape format
        "quiet": False,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            songdata = ydl.extract_info(url, download=True)

        print("\n========= Extract video info cleanly =========")
        wanted_keys = ["id", "title", "author", "album", "thumbnail", "description",
                       "webpage_url", "view_count", "upload_date", "categories", "tags",
                       "publishDate", "videoDetails"]

        for key in wanted_keys:
            value = songdata.get(key)
            if key == "id":
                video_id = value
        print("========= Extract video info cleanly =========\n")

        # Optional: fetch additional metadata from utils
        song_data_ytl = get_song_by_id(video_id)

        ytl_keys = ["videoId", "title", "artist", "coverUrl", "description",
                    "urlCanonical", "viewCount", "publishDate", "category", "tags"]

        for key in ytl_keys:
            ytl_value = song_data_ytl.get(key)

            if key == "videoId":
                video_id = ytl_value
                print(f"{key}: {video_id}")

            elif key == "title":
                title = ytl_value
                print(f"{key}: {title}")

            elif key == "artist":  # ✅ fixed (was author)
                artist = ytl_value
                print(f"{key}: {artist}")

            elif key == "tags":
                tags = ytl_value
                print(f"{key}: {tags}")

            elif key == "publishDate":  # ✅ fixed variable name
                publishdate = ytl_value
                print(f"{key}: {publishdate}")

        # Prepare file paths
        temp_filepath = os.path.join(DOWNLOAD_FOLDER, f"{video_id}.mp3")
        safe_title = sanitize_filename(title)
        safe_artist = sanitize_filename(artist)
        final_filepath = os.path.join(DOWNLOAD_FOLDER, f"{safe_title} - {safe_artist}.mp3")

        # Rename file
        if os.path.exists(temp_filepath):
            os.rename(temp_filepath, final_filepath)
        else:
            print(f"[ERROR] Expected file not found: {temp_filepath}")
            return

        # ID3 tagging
        try:
            audio = EasyID3(final_filepath)
        except ID3NoHeaderError:
            ID3().save(final_filepath)
            audio = EasyID3(final_filepath)

        audio["title"] = title
        audio["artist"] = artist
        if tags:
            audio["composer"] = ", ".join(tags) if isinstance(tags, list) else str(tags)
        audio.save(v2_version=3)

        # Add videoId and release date using ID3
        id3 = ID3(final_filepath)
        if video_id:
            id3.add(TKEY(encoding=3, text=video_id))
        if publishdate:
            date_only = publishdate.split("T")[0].replace("-", "")
            id3.add(COMM(encoding=3, lang='eng', desc='ReleasedDate', text=date_only))
        id3.save(v2_version=3)

        print(f"✅ Downloaded & tagged: {final_filepath}\n")

    except Exception as e:
        print(f"[ERROR] Failed to download '{title}' from {url}: {e}")


def main():
    json_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".json")]
    if not json_files:
        print("[INFO] No JSON files found in data/ folder.")
        return

    for json_file in json_files:
        filepath = os.path.join(DATA_FOLDER, json_file)
        album_name = os.path.splitext(json_file)[0]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                songs = json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not read {filepath}: {e}")
            continue

        for song in songs:
            download_mp3(song, album=album_name)


if __name__ == "__main__":
    main()
