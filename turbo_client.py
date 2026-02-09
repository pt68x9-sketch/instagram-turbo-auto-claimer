import aiohttp
import asyncio
from datetime import datetime
import requests
import json
from pathlib import Path
import logging
import sys
import os

USERNAMES = ["alpha", "beta", "gamma", "delta"]

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATS_FILE = Path("stats.json")
LOG_FILE = Path("turbo_client.log")

# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# ASCII Skull Logo
LOGO = r"""
      .ed"""" """$$$.
    -"           ^""**$$.
  ."                   '$$
 /                      "4$
d  3                      $$$$
$  *                   .$$$$$$
d  .$$@$$$.        $$$$$$$$
$  $$$$$$$$$$"       $$$$$$$$$
*  $$$$$$$$$$       $$$$$$$$$$
$  $$$$$$$$$.     $$$$$$$$$$
$  $$$$$$$$$$$.   $$$$$$$$$$
$  $$$$$$$$$$$$$$$$$$$$$$$$
*  $$$$$$$$$$$$$$$$$$$$$$$$$
 $  $$$$$$$$$$$$$$$$$$$$$$$
  *  $$$$$$$$$$$$$$$$$$$$$"
    "$$$$$$$$$$$$$$$$$$$"
       "^$$$$$$$$$$$$$$"
          "$$$$$$$$$$"
            """""""""
"""

print(LOGO)
logging.info("Starting turbo client...")

# Initialize or load stats
try:
    stats = json.loads(STATS_FILE.read_text())
except Exception:
    stats = {
        "attempts": 0,
        "claimed_usernames": [],
        "history": []
    }

def save_stats():
    STATS_FILE.write_text(json.dumps(stats))

def update_stats(attempt_increment=0, claimed_name=None):
    stats["attempts"] += attempt_increment
    if claimed_name and claimed_name not in stats["claimed_usernames"]:
        stats["claimed_usernames"].append(claimed_name)
    stats["history"].append({
        "time": datetime.now().isoformat(),
        "attempts": stats["attempts"]
    })
    stats["history"] = stats["history"][-200:]  # Keep last 200 records
    save_stats()

def send_discord_alert(message):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except Exception as e:
        logging.error(f"Discord alert error: {e}")

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        logging.error(f"Telegram alert error: {e}")

async def check_name(session, name):
    try:
        async with session.get(f"http://127.0.0.1:8000/check/{name}") as resp:
            data = await resp.json()
            return data["available"]
    except Exception as e:
        logging.error(f"Error checking {name}: {e}")
        return False

async def claim_name(session, name):
    try:
        async with session.post(f"http://127.0.0.1:9000/assign/{name}") as resp:
            data = await resp.json()
            return data["status"] == "success"
    except Exception as e:
        logging.error(f"Error claiming {name}: {e}")
        return False

async def monitor(name, session):
    while True:
        try:
            update_stats(attempt_increment=1)
            if await check_name(session, name):
                claimed = await claim_name(session, name)
                if claimed:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    message = f"🚀 [{timestamp}] SNIPED username: {name}"
                    logging.info(message)
                    send_discord_alert(message)
                    send_telegram_alert(message)
                    update_stats(claimed_name=name)
            await asyncio.sleep(0.2)
        except Exception as e:
            logging.error(f"Error monitoring {name}: {e}")
            await asyncio.sleep(1)

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(monitor(name, session)) for name in USERNAMES]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())