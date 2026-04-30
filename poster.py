import os, json, random, requests, time
from pathlib import Path

IG_USER_ID    = os.environ["IG_USER_ID"]
ACCESS_TOKEN  = os.environ["IG_ACCESS_TOKEN"]
REPO          = os.environ["GITHUB_REPOSITORY"]
REELS_FOLDER  = "reels"
CAPTIONS_FILE = "captions.txt"
LOG_FILE      = "posted_log.json"

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

def get_video_url(filename):
    return f"https://raw.githubusercontent.com/{REPO}/main/reels/{filename}"

def create_container(video_url, caption):
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={"media_type": "REELS", "video_url": video_url,
              "caption": caption, "access_token": ACCESS_TOKEN}
    )
    r.raise_for_status()
    return r.json()["id"]

def wait_for_ready(cid):
    params = {"fields": "status_code", "access_token": ACCESS_TOKEN}
    for _ in range(18):
        r = requests.get(f"https://graph.facebook.com/v19.0/{cid}", params=params)
        status = r.json().get("status_code")
        print(f"Status: {status}")
        if status == "FINISHED": return True
        if status == "ERROR": return False
        time.sleep(10)
    return False

def publish(cid):
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": ACCESS_TOKEN}
    )
    r.raise_for_status()
    return r.json()["id"]

def main():
    log      = load_log()
    captions = load_captions()
    reel     = get_next_reel(log)

    if not reel:
        print("✅ Saari reels post ho gayi! Naye daalo.")
        return

    caption = random.choice(captions)
    url     = get_video_url(reel.name)

    print(f"📹 Posting: {reel.name}")
    print(f"📝 Caption: {caption}")

    cid = create_container(url, caption)
    print(f"⏳ Container: {cid}")

    if wait_for_ready(cid):
        post_id = publish(cid)
        print(f"✅ Posted! ID: {post_id}")
        log["posted"].append(reel.name)
        save_log(log)
    else:
        print("❌ Failed — agli baar try hoga")

if __name__ == "__main__":
    main()
