from flask import Flask, request, jsonify
import json
from pathlib import Path
from instagrapi import Client
import threading
import time

app = Flask(__name__)
ACCOUNT_POOL_FILE = Path("instagram_account_pool.json")
LOCK = threading.Lock()

# Load accounts
try:
    account_pool = json.loads(ACCOUNT_POOL_FILE.read_text())
except Exception:
    account_pool = []

def save_accounts():
    ACCOUNT_POOL_FILE.write_text(json.dumps(account_pool))

def assign_username_to_account(username):
    with LOCK:
        for account in account_pool:
            if not account.get("in_use", False):
                account["in_use"] = True
                save_accounts()
                try:
                    cl = Client()
                    cl.login(account["username"], account["password"])
                    cl.username_change(username)
                    cl.logout()
                    account["in_use"] = False
                    save_accounts()
                    return True
                except Exception as e:
                    account["in_use"] = False
                    save_accounts()
                    print(f"Error assigning username {username} to {account['username']}: {e}")
                    return False
        return False

@app.route("/assign/<username>", methods=["POST"])
def assign_username(username):
    success = assign_username_to_account(username)
    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failure"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)