import os
import json
from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
import sys
import io
from mutagen.id3 import ID3, ID3NoHeaderError, TKEY

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "Download_Songs"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def sanitize_filename(name):
    if not name:
        name = "Unknown"
    return "".join(c for c in name if c.isalnum() or c in " ._-").rstrip()


def download_mp3(song, album=None):
    url = song.get("urlCanonical") or (f"https://music.youtube.com/watch?v={song.get('videoId')}" if song.get('videoId') else None)
    if not url:
        print(f"[SKIP] No valid URL for: {song.get('title', 'Unknown')}")
        return

    fallback_title = song.get("title") or "Unknown Title"
    fallback_artist = song.get("artist") or "Unknown Artist"
    tags = song.get("tags") or []
    publishdate = song.get("publishDate")
    video_id = song.get("videoId")  # ✅ Grab videoId


    safe_title = sanitize_filename(fallback_title)
    safe_artist = sanitize_filename(fallback_artist)
    filename = f"{safe_title} - {safe_artist}.mp3"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    if os.path.exists(filepath):
        print(f"[SKIP] {filename} already exists")
        return

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filepath.replace(".mp3", ".%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        "quiet": False,
        "no_warnings": True,
        "cookiefile": "cookies.txt"  # GitHub secret cookie file
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = info.get("title") or fallback_title
        artist = info.get("artist") or info.get("uploader") or fallback_artist
        ytd_tags = info.get("tags") or tags

        try:
            audio = EasyID3(filepath)
        except ID3NoHeaderError:
            ID3().save(filepath)
            audio = EasyID3(filepath)

        if title:
            audio["title"] = fallback_title
        if fallback_artist:
            audio["artist"] = fallback_artist
        if ytd_tags:
            audio["composer"] = ", ".join(ytd_tags) if isinstance(ytd_tags, list) else str(ytd_tags)
        if publishdate:
            date_only = publishdate.split("T")[0]
            date_no_dash = date_only.replace("-", "")
            audio["date"] = date_no_dash

        audio.save(v2_version=3)

        if video_id:
            id3 = ID3(filepath)
            id3.add(TKEY(encoding=3, text=video_id))
            id3.save(v2_version=3)

            
        print(f"✅ Downloaded & tagged: {filename} | Title: {title} | Artist: {artist}")

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
