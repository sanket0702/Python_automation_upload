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


def download_mp3(videoId, title, artist, coverUrl, description,
                  urlCanonical, viewCount, publishDate, category, tags,
                  output_folder):
    # Construct URL
    url = urlCanonical or (
        f"https://music.youtube.com/watch?v={videoId}" if videoId else None
    )
    if not url:
        print(f"[SKIP] No valid URL for: {title}")
        return

    # Extract basic info
    #title = song.get("title") or "Unknown Title"
    #artist = song.get("artist") or "Unknown Artist"
    ##tags = song.get("tags") or []
    #publishdate = song.get("publishDate")
    #video_id = song.get("videoId")
    #coverUrl = song.get("coverUrl", "")
    
    print(f"✅ Starting download: {title} | Artist: {artist} | VideoID: {videoId}")

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
        song_data_ytl = get_song_by_id(videoId)
        """
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
        """
        # Prepare file paths
        temp_filepath = os.path.join(DOWNLOAD_FOLDER, f"{videoId}.mp3")
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
            id3.add(TKEY(encoding=3, text=videoId))
        if publishDate:
            date_only = publishDate.split("T")[0].replace("-", "")
            id3.add(COMM(encoding=3, lang='eng', desc='ReleasedDate', text=date_only))
        id3.save(v2_version=3)

        print(f"✅ Downloaded & tagged: {final_filepath}\n")

    except Exception as e:
        print(f"[ERROR] Failed to download '{title}' from {url}: {e}")


def scan_and_download(tracks_file="data/tracks.json"):
    if not os.path.exists(tracks_file):
        print(f"[ERROR] {tracks_file} not found")
        return

    with open(tracks_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to read {tracks_file}: {e}")
            return

    if not isinstance(data, list):
        print(f"[ERROR] {tracks_file} does not contain a list")
        return

    output_folder = os.path.join("Download_Songs")
    os.makedirs(output_folder, exist_ok=True)

    for item in data:
        if not isinstance(item, dict):
            continue

        videoId = item.get("videoId")
        title = item.get("title")
        artist = item.get("artist")
        coverUrl = item.get("coverUrl")
        description = item.get("description")
        urlCanonical = item.get("urlCanonical")
        viewCount = item.get("viewCount")
        publishDate = item.get("publishDate")
        category = item.get("category")
        tags = item.get("tags")

        if not title or not artist:
            continue

        print(f"[INFO] Downloading {title} - {artist} -> {output_folder}")
        
        # Call your download function with all required fields
        download_mp3(
            videoId=videoId,
            title=title,
            artist=artist,
            coverUrl=coverUrl,
            description=description,
            urlCanonical=urlCanonical,
            viewCount=viewCount,
            publishDate=publishDate,
            category=category,
            tags=tags,
            output_folder=output_folder
        )



def main():
    scan_and_download()
    


if __name__ == "__main__":
    main()
