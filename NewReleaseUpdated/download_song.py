import os
import json
from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
import re

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "Download_Songs"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def clean_title(title):
    if not title:
        return "Unknown Title"
    # Remove parentheses and their content
    title = re.sub(r"\s*\(.*?\)", "", title)
    # Remove anything after '-' or '|'
    title = re.split(r"[-|]", title)[0]
    return title.strip()

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in " ._-").rstrip()


def download_mp3(song, album=None):
    # Resolve URL (prefer urlCanonical, fallback to videoId)
    url = song.get("urlCanonical")
    if not url:
        video_id = song.get("videoId")
        if video_id:
            url = f"https://music.youtube.com/watch?v={video_id}"
        else:
            print(f"[SKIP] No valid URL for: {song.get('title', 'Unknown')}")
            return

    # Fallback metadata from JSON
    fallback_title = song.get("title", "Unknown Title")
    fallback_title = clean_title(fallback_title)
    fallback_artist = song.get("artist", "Unknown Artist")
    tags = song.get("tags") or []
    publishdate = song.get("publishDate") 

    # Build safe target path (we will instruct yt_dlp to create final mp3 at this exact path)
    safe_title = sanitize_filename(fallback_title)
    safe_artist = sanitize_filename(fallback_artist)
    filename = f"{safe_title} - {safe_artist}.mp3"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    if os.path.exists(filepath):
        print(f"[SKIP] {filename} already exists")
        return

    ydl_opts = {
        "format": "bestaudio/best",
        # create a temporary file with the same name but proper extension replacement
        "outtmpl": filepath.replace(".mp3", ".%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": False,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # extract_info returns metadata dict and will download
            info = ydl.extract_info(url, download=True)

        # Use yt_dlp metadata if available (prefer this)
        title = info.get("title") or fallback_title
        artist = info.get("artist") or info.get("uploader") or fallback_artist
        # tags from yt_dlp if available, else from JSON
        ytd_tags = info.get("tags") or tags

        # mp3_path is where our mp3 should be (outtmpl ensures this)
        mp3_path = filepath

        # Ensure ID3 header exists: open EasyID3, create header if missing
        try:
            audio = EasyID3(mp3_path)
        except ID3NoHeaderError:
            # create empty ID3 header then re-open
            ID3().save(mp3_path)
            audio = EasyID3(mp3_path)
        except Exception as e:
            # unexpected exception when opening tags
            print(f"[WARN] Could not open ID3 tags initially: {e}. Attempting to create header.")
            try:
                ID3().save(mp3_path)
                audio = EasyID3(mp3_path)
            except Exception as ee:
                print(f"[ERROR] Failed to create ID3 header: {ee}")
                return

        # Assign tags (EasyID3 accepts string or list of strings)
        try:

            if title:
                audio["title"] = safe_title
            if fallback_artist:
                audio["artist"] = fallback_artist
            #if album:
               # audio["album"] = album
            # composer stores tags/genres — store as single string
            if ytd_tags:
                if isinstance(ytd_tags, list):
                    audio["composer"] = ", ".join(ytd_tags)
                else:
                    audio["composer"] = str(ytd_tags)
            # publish date (use 'date' key)
            # publish date (use 'date' key)
            if publishdate:
                date_only = publishdate.split("T")[0]  # "2025-05-01"
                date_no_dash = date_only.replace("-", "")  # "20250501"
                audio["date"] = date_no_dash


            audio.save(v2_version=3)  # save as ID3v2.3 for broad compatibility
        except Exception as e:
            print(f"[ERROR] Failed to write ID3 tags for {mp3_path}: {e}")
            return

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
        album_name = os.path.splitext(json_file)[0]  # use filename as album/playlist name
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
