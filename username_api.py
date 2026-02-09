from flask import Flask, jsonify
import json
from pathlib import Path

app = Flask(__name__)
USERNAMES_FILE = Path("usernames.json")

# Load usernames and availability
try:
    usernames_data = json.loads(USERNAMES_FILE.read_text())
except Exception:
    usernames_data = {"usernames": [], "available": {}}

@app.route("/check/<name>")
def check_name(name):
    available = usernames_data.get("available", {}).get(name, False)
    return jsonify({"available": available})

@app.route("/claim/<name>", methods=["POST"])
def claim_name(name):
    if usernames_data["available"].get(name, False):
        usernames_data["available"][name] = False
        # Save changes
        USERNAMES_FILE.write_text(json.dumps(usernames_data))
        return jsonify({"status": "claimed"})
    return jsonify({"status": "failed"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
