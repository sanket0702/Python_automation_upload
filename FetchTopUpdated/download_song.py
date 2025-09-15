import os
import json
from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError, TKEY,TDRC,COMM
import sys
import io

# Ensure stdout/stderr handles UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "Download_Songs"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def sanitize_filename(name):
    if not name:
        name = "Unknown"
    # Remove invalid characters for filesystem
    return "".join(c for c in name if c.isalnum() or c in " ._-").rstrip()


def download_mp3(song, album=None):
    url = song.get("urlCanonical") or (
        f"https://music.youtube.com/watch?v={song.get('videoId')}"
        if song.get("videoId")
        else None
    )
    if not url:
        print(f"[SKIP] No valid URL for: {song.get('title', 'Unknown')}")
        return

    title = song.get("title") or "Unknown Title"
    print(f"[ERROR] Could not read TITLE= {title}: ")
    artist = song.get("artist") or "Unknown Artist"
    print(f"[ERROR] Could not read ARTIST =={artist}: ")
    tags = song.get("tags") or []
    publishdate = song.get("publishDate")
    print(f"[ERROR] Could not read RELEASEdATE =={publishdate}:")
    video_id = song.get("videoId")

    print(f"✅ Starting download: {title} | Artist: {artist} | VideoID: {video_id}")

    # Output template (temporary name, will rename later)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "cookiefile": "cookies.txt",  # must be Netscape format
        "quiet": False,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # File path that yt-dlp created (by video ID)
        temp_filepath = os.path.join(DOWNLOAD_FOLDER, f"{info['id']}.mp3")

        # Final safe filename
        safe_title = sanitize_filename(title)
        safe_artist = sanitize_filename(artist)
        final_filepath = os.path.join(
            DOWNLOAD_FOLDER, f"{safe_title} - {safe_artist}.mp3"
        )

        if os.path.exists(temp_filepath):
            os.rename(temp_filepath, final_filepath)
        else:
            print(f"[ERROR] Expected file not found: {temp_filepath}")
            return

        # --- ID3 Tagging ---
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

        # Add videoId as TKEY
        if video_id:
            id3 = ID3(final_filepath)
            id3.add(TKEY(encoding=3, text=video_id))
            id3.save(v2_version=3)

        if publishdate:
            id3 = ID3(final_filepath)
            date_only = publishdate.split("T")[0]  # "2025-05-01"
            date_no_dash = date_only.replace("-", "")  # "20250501"
            id3.add(COMM(encoding=3, lang='eng', desc='ReleasedDate', text=date_no_dash))
            
            #id3.add(TDRC(encoding=3, text=date_no_dash))
            id3.save(v2_version=3)


        print(f"✅ Downloaded & tagged: {final_filepath}")

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
