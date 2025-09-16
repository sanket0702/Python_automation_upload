import json
import os

def convert_cookies_to_headers(cookies_txt: str, output_file="headers_auth.json"):
    lines = cookies_txt.strip().splitlines()
    cookie_str = "; ".join([
        line.split("\t")[-2] + "=" + line.split("\t")[-1]
        for line in lines if not line.startswith("#") and line.strip()
    ])

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://music.youtube.com",
        "Cookie": cookie_str
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(headers, f, indent=2)

    print(f"✅ Generated {output_file}")

if __name__ == "__main__":
    cookies_env = os.getenv("YTMUSIC_COOKIES") or os.getenv("YTM_COOKIES")
    if not cookies_env:
        raise ValueError("❌ Missing YTM_COOKIES secret")
    convert_cookies_to_headers(cookies_env)
