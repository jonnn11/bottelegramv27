from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from telethon import TelegramClient
import threading
import time
import os

app = Flask(__name__, static_folder=".")
CORS(app)

client = None
running = False
history = {}

# ================= FRONTEND =================
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# ================= TELEGRAM LOGIN =================
@app.route("/send_code", methods=["POST"])
def send_code():
    global client

    data = request.json
    client = TelegramClient("session", int(data["api_id"]), data["api_hash"])
    client.connect()
    client.send_code_request(data["phone"])
    client.phone = data["phone"]

    return jsonify({"status": "ok", "message": "OTP terkirim"})

@app.route("/verify", methods=["POST"])
def verify():
    code = request.json["code"]
    client.sign_in(client.phone, code)
    return jsonify({"status": "ok", "message": "Login sukses"})

# ================= START SENDER =================
@app.route("/start", methods=["POST"])
def start():
    global running
    running = True

    data = request.json
    targets = data["targets"]
    delay = float(data.get("delay", 3))
    cid = data.get("client_id", "default")

    history.setdefault(cid, [])

    def worker():
        global running
        while running:
            for t in targets:
                for g in t["groups"]:
                    if not running:
                        return
                    try:
                        client.send_message(g, t["message"])
                        history[cid].append({
                            "group": g,
                            "message": t["message"],
                            "status": "sent"
                        })
                    except:
                        history[cid].append({
                            "group": g,
                            "message": t["message"],
                            "status": "failed"
                        })
                    time.sleep(delay)

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"status": "ok", "message": "running"})

# ================= STOP =================
@app.route("/stop", methods=["POST"])
def stop():
    global running
    running = False
    return jsonify({"status": "ok", "message": "stopped"})

# ================= HISTORY =================
@app.route("/history", methods=["POST"])
def get_history():
    cid = request.json.get("client_id", "default")
    return jsonify(history.get(cid, []))

# ================= IMPORTANT FIX =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)