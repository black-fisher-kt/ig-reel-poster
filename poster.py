import os
import json
import random
import requests
import time
from pathlib import Path

# ── Config ──────────────────────────────────────────
IG_USER_ID    = os.environ["IG_USER_ID"]
ACCESS_TOKEN  = os.environ["IG_ACCESS_TOKEN"]
REPO          = os.environ["GITHUB_REPOSITORY"]
REELS_FOLDER  = "reels"
CAPTIONS_FILE = "captions.txt"
LOG_FILE      = "posted_log.json"
API_VERSION   = "v21.0"
BASE_URL      = f"https://graph.facebook.com/{API_VERSION}"

# ── Load captions ────────────────────────────────────
def load_captions():
    with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# ── Load/Save log ────────────────────────────────────
def load_log():
    if Path(LOG_FILE).exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"posted": []}

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

# ── Get next unposted reel ───────────────────────────
def get_next_reel(log):
    all_reels = sorted(Path(REELS_FOLDER).glob("*.mp4"))
    for reel in all_reels:
        if reel.name not in log["posted"]:
            return reel
    return None

# ── Video URL ────────────────────────────────────────
def get_video_url(filename):
    return f"https://raw.githubusercontent.com/{REPO}/main/reels/{filename}"

# ── Create container ─────────────────────────────────
def create_container(video_url, caption):
    url = f"{BASE_URL}/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": ACCESS_TOKEN,
    }
    r = requests.post(url, data=payload)
    print(f"Container API Response: {r.status_code} - {r.text}")
    r.raise_for_status()
    return r.json()["id"]

# ── Wait for ready ───────────────────────────────────
def wait_for_ready(container_id, max_wait=180):
    url = f"{BASE_URL}/{container_id}"
    params = {
        "fields": "status_code,status",
        "access_token": ACCESS_TOKEN
    }
    for i in range(max_wait // 10):
        r = requests.get(url, params=params)
        data = r.json()
        status = data.get("status_code")
        print(f"  [{i+1}] Status: {status} | {data.get('status', '')}")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            print(f"  Error details: {data}")
            return False
        time.sleep(10)
    return False

# ── Publish ──────────────────────────────────────────
def publish(container_id):
    url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": ACCESS_TOKEN,
    }
    r = requests.post(url, data=payload)
    print(f"Publish API Response: {r.status_code} - {r.text}")
    r.raise_for_status()
    return r.json()["id"]

# ── Main ─────────────────────────────────────────────
def main():
    log      = load_log()
    captions = load_captions()
    reel     = get_next_reel(log)

    if not reel:
        print("✅ Saari reels post ho gayi! Naye daalo.")
        return

    caption   = random.choice(captions)
    video_url = get_video_url(reel.name)

    print(f"📹 Posting: {reel.name}")
    print(f"🔗 URL: {video_url}")
    print(f"📝 Caption: {caption}")

    try:
        cid = create_container(video_url, caption)
        print(f"⏳ Container ID: {cid}")

        if wait_for_ready(cid):
            post_id = publish(cid)
            print(f"✅ Posted! ID: {post_id}")
            log["posted"].append(reel.name)
            save_log(log)
        else:
            print("❌ Container processing failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
