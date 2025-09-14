import os
import json
from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "Download_Songs"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def validate_json():
    json_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".json")]
    for file in json_files:
        path = os.path.join(DATA_FOLDER, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                songs = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load {file}: {e}")
            continue

        for idx, song in enumerate(songs):
            if not isinstance(song, dict):
                print(f"[ERROR] Invalid song entry at index {idx} in {file}")
            if not song.get("urlCanonical") and not song.get("videoId"):
                print(f"[WARN] No URL or videoId for song at index {idx} in {file}")
            if not song.get("title"):
                print(f"[WARN] Missing title at index {idx} in {file}")
            if not song.get("artist") and not (song.get("videoDetails") or {}).get("author"):
                print(f"[WARN] Missing artist at index {idx} in {file}")

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in " ._-").rstrip()


DRY_RUN = True  # set False to actually download

def download_mp3(song, album=None):
    try:
        # Resolve URL
        url = song.get("urlCanonical") or f"https://music.youtube.com/watch?v={song.get('videoId')}"
    except Exception as e:
        print(f"[ERROR] URL missing: {e}, song: {song}")
        return

    # Metadata
    fallback_title = song.get("title") or "Unknown Title"
    fallback_artist = song.get("artist") or "Unknown Artist"
    video_details = song.get("videoDetails") or {}
    fallback_artist = video_details.get("author") or fallback_artist
    publishdate = song.get("publishDate") or video_details.get("publishDate")
    tags = song.get("tags") or []

    # Sanitize
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
                audio["title"] = fallback_title
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

    validate_json()
    main()
