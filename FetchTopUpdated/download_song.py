import os
import json
from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError, TKEY
import sys
import io

# Ensure stdout/stderr handles UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "Download_Songs"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def sanitize_filename(name):
    if not name:
        name = "Unknown"
    # Remove invalid characters for filesystem
    return "".join(c for c in name if c.isalnum() or c in " ._-").rstrip()


def download_mp3(song, album=None):
    url = song.get("urlCanonical") or (f"https://music.youtube.com/watch?v={song.get('videoId')}" if song.get("videoId") else None)
    if not url:
        print(f"[SKIP] No valid URL for: {song.get('title', 'Unknown')}")
        return

    fallback_title = song.get("title") or "Unknown Title"
    fallback_artist = song.get("artist") or "Unknown Artist"
    tags = song.get("tags") or []
    publishdate = song.get("publishDate")
    video_id = song.get("videoId")  # ✅ Save videoId for ID3

    print(f"✅ Starting download: {fallback_title} | Artist: {fallback_artist} | VideoID: {video_id}")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
        "cookiefile": "cookies.txt",  # must be Netscape format
        "quiet": False,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Get the actual filename yt-dlp used
        filepath = ydl.prepare_filename(info)
        filepath = os.path.splitext(filepath)[0] + ".mp3"

        # Sanitize filename to avoid special characters
        safe_title = sanitize_filename(fallback_title)
        safe_artist = sanitize_filename(fallback_artist)
        safe_filepath = os.path.join(DOWNLOAD_FOLDER, f"{safe_title} - {safe_artist}.mp3")

        artist=info.get("artist") or fallback_artist
        # Rename file to sanitized version
        if os.path.exists(filepath):
            os.rename(filepath, safe_filepath)
        filepath = safe_filepath

        # ID3 tagging
        try:
            audio = EasyID3(filepath)
        except ID3NoHeaderError:
            ID3().save(filepath)
            audio = EasyID3(filepath)

        audio["title"] = fallback_title
        audio["artist"] = artist
        if tags:
            audio["composer"] = ", ".join(tags) if isinstance(tags, list) else str(tags)
        if publishdate:
            date_only = publishdate.split("T")[0]
            audio["date"] = date_only.replace("-", "")
            audio.save(v2_version=3)

        # Add videoId as TKEY
        if video_id:
            id3 = ID3(filepath)
            id3.add(TKEY(encoding=3, text=video_id))
            id3.save(v2_version=3)

        print(f"✅ Downloaded & tagged: {filepath}")

    except Exception as e:
        print(f"[ERROR] Failed to download '{fallback_title}' from {url}: {e}")


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