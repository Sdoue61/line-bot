import os, csv, hmac, hashlib, base64, json, datetime
from flask import Flask, request
import requests

app = Flask(__name__)

LINE_ACCESS = os.environ["LINE_ACCESS_TOKEN"]
LINE_SECRET = os.environ["LINE_CHANNEL_SECRET"]

DATA_DIR = "/data"
USERS_FILE = f"{DATA_DIR}/users.csv"
ADMINS_FILE = f"{DATA_DIR}/admins.txt"
CAR_FILE = f"{DATA_DIR}/car_usage.csv"
FAQ_FILE = f"{DATA_DIR}/faq.csv"

# ----------------------
# Utilities
# ----------------------

def reply(token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS}",
        "Content-Type": "application/json"
    }
    data = {
        "replyToken": token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, json=data)

def load_admins():
    if not os.path.exists(ADMINS_FILE):
        return []
    return [x.strip() for x in open(ADMINS_FILE)]

def get_user_name(user_id):
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE) as f:
        for row in csv.reader(f):
            if row[0] == user_id:
                return row[1]
    return None

def log_car(date, user):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CAR_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, user, datetime.datetime.now()])

def is_car_report(msg):
    keys = ["car", "車", "社用車", "運転"]
    return any(k in msg.lower() for k in keys)

# ----------------------
# Webhook
# ----------------------

@app.route("/callback", methods=["POST"])
def callback():
    body = request.json
    event = body["events"][0]
    msg = event["message"]["text"]
    token = event["replyToken"]
    user_id = event["source"]["userId"]

    admins = load_admins()
    name = get_user_name(user_id) or "Staff"

    # Admin commands
    if msg.lower() == "/whoami":
        reply(token, f"Your LINE ID:\n{user_id}")
        return "OK"

    # Car usage
    if is_car_report(msg):
        today = datetime.date.today().isoformat()
        log_car(today, name)
        reply(token, "🚗 社用車の使用を記録しました。")
        return "OK"

    # Simple FAQ
    if "salary" in msg.lower() or "給料" in msg:
        reply(token, "給与は毎月15日に支払われます。")
        return "OK"

    if "shift" in msg.lower() or "シフト" in msg:
        reply(token, "シフトはGoogleシートで確認できます。")
        return "OK"

    reply(token, "ご質問をもう少し詳しく教えてください。")
    return "OK"
