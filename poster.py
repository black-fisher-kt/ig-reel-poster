import os, json, random, time
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

USERNAME     = os.environ["IG_USERNAME"]
PASSWORD     = os.environ["IG_PASSWORD"]
REELS_FOLDER = "reels"
CAPTIONS_FILE = "captions.txt"
LOG_FILE     = "posted_log.json"
SESSION_FILE = "session.json"

def load_captions():
    with open(CAPTIONS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_log():
    if Path(LOG_FILE).exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"posted": []}

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def get_next_reel(log):
    all_reels = sorted(Path(REELS_FOLDER).glob("*.mp4"))
    for reel in all_reels:
        if reel.name not in log["posted"]:
            return reel
    return None

def login():
    cl = Client()
    cl.delay_range = [1, 3]
    if Path(SESSION_FILE).exists():
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            cl.get_timeline_feed()
            print("✅ Session se login hua")
            return cl
        except LoginRequired:
            print("⚠️ Session expired, fresh login...")
    cl.login(USERNAME, PASSWORD)
    cl.dump_settings(SESSION_FILE)
    print("✅ Fresh login hua")
    return cl

def main():
    log      = load_log()
    captions = load_captions()
    reel     = get_next_reel(log)

    if not reel:
        print("✅ Saari reels post ho gayi! Naye daalo.")
        return

    caption = random.choice(captions)
    print(f"📹 Posting: {reel.name}")
    print(f"📝 Caption: {caption}")

    cl = login()
    media = cl.clip_upload(reel, caption)
    print(f"✅ Posted! ID: {media.id}")

    log["posted"].append(reel.name)
    save_log(log)

if __name__ == "__main__":
    main()
